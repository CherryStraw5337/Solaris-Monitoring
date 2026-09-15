# Integración ESP32 con API Solaris Monitoring

## Visión General

Guía para conectar un ESP32 a la API de monitoreo de celdas fotovoltaicas. El dispositivo IoT leerá voltaje de un sensor y enviará datos a la API cada 5 minutos.

---

## Hardware Necesario

- **ESP32** (DevKit v1 o similar)
- **Sensor de Voltaje**: Divisor de voltaje o sensor ACS712
- **Celda Fotovoltaica** (o fuente de voltaje variable)
- **Cable USB** para programación
- **WiFi** disponible

### Conexión Física

```
Celda Fotovoltaica → Divisor de Voltaje → GPIO A0 (ADC)
                                       → GND
5V (internal)                          → 3.3V
GND                                    → GND
```

---

## Código Arduino/MicroPython

### Opción 1: Arduino IDE

**Instalación de Librerías:**
1. Sketch → Include Library → Manage Libraries
2. Buscar: "ArduinoHttpClient" y "AsyncWifi"
3. Instalar ambas

**Sketch Completo:**

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <Arduino.h>

// ===== Configuración =====
const char* SSID = "TU_SSID";
const char* PASSWORD = "TU_PASSWORD";
const char* API_URL = "http://solaris-monitoring-api.onrender.com";
const int CELL_ID = 1;  // ID de la celda en la API
const int ADC_PIN = A0; // GPIO 36
const int INTERVAL_MS = 300000; // 5 minutos

// Configuración de ADC
const float REF_VOLTAGE = 3.3;
const int ADC_MAX = 4095;

unsigned long last_send = 0;

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println("\n\nIniciando ESP32...");
    connect_wifi();
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connect_wifi();
    }

    // Enviar cada 5 minutos
    if (millis() - last_send > INTERVAL_MS) {
        send_reading();
        last_send = millis();
    }

    delay(1000);
}

void connect_wifi() {
    Serial.printf("Conectando a WiFi: %s\n", SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi conectado!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nError: No se pudo conectar a WiFi");
    }
}

void send_reading() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi desconectado, saltando lectura");
        return;
    }

    // Leer voltaje
    int raw_adc = analogRead(ADC_PIN);
    float voltage = (raw_adc / (float)ADC_MAX) * REF_VOLTAGE;

    Serial.printf("ADC Raw: %d, Voltaje: %.2f V\n", raw_adc, voltage);

    // Crear JSON
    String payload = "{\"cell_id\":" + String(CELL_ID) +
                     ",\"voltage_measured\":" + String(voltage, 2) + "}";

    // Enviar a API
    HTTPClient http;
    String url = String(API_URL) + "/api/v1/readings";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    int httpCode = http.POST(payload);

    if (httpCode == 201) {
        Serial.println("✓ Lectura enviada exitosamente");
        String response = http.getString();
        Serial.println("Respuesta: " + response);
    } else {
        Serial.printf("✗ Error HTTP: %d\n", httpCode);
        Serial.println("Payload: " + payload);
    }

    http.end();
}
```

**Instrucciones:**
1. Abrir Arduino IDE
2. Tools → Board: "ESP32 Dev Module"
3. Tools → Port: seleccionar puerto COM
4. Modificar SSID, PASSWORD, API_URL, CELL_ID
5. Upload

---

### Opción 2: MicroPython

**Instalación:**
1. Descargar firmware de micropython para ESP32
2. Usar esptool.py para flashear
3. Usar Thonny IDE para editar

**Script MicroPython:**

```python
import network
import urequests
import machine
import time
import json
from machine import ADC, Pin

# ===== Configuración =====
#include <WiFi.h>
#include <HTTPClient.h>
#include <Arduino.h>

// ===== Configuración =====
const char* SSID = "SSID";
const char* PASSWORD = "PASSWORD";
const char* API_URL = "https://solaris-monitoring-api.onrender.com";
const int CELL_ID = 1;  // ID de la celda en la API
const int ADC_PIN = 2;  // GPIO 2 (ADC1_CH2 para ESP32-C6)
const int INTERVAL_MS = 10000; // 10 segundos (para pruebas rápidas)

// Configuración de ADC
const float REF_VOLTAGE = 3.3;
const int ADC_MAX = 4095;

unsigned long last_send = 0;

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println("\n\nIniciando ESP32...");
    connect_wifi();
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connect_wifi();
    }

    // Enviar cada 10 segundos
    if (millis() - last_send > INTERVAL_MS) {
        send_reading();
        last_send = millis();
    }

    delay(1000);
}

void connect_wifi() {
    Serial.printf("Conectando a WiFi: %s\n", SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi conectado!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nError: No se pudo conectar a WiFi");
    }
}

void send_reading() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi desconectado, saltando lectura");
        return;
    }

    // Leer voltaje
    int raw_adc = analogRead(ADC_PIN);
    float voltage = (raw_adc / (float)ADC_MAX) * REF_VOLTAGE;

    Serial.printf("ADC Raw: %d, Voltaje: %.2f V\n", raw_adc, voltage);

    // Crear JSON
    String payload = "{\"cell_id\":" + String(CELL_ID) +
                     ",\"voltage_measured\":" + String(voltage, 2) + "}";

    // Enviar a API
    HTTPClient http;
    String url = String(API_URL) + "/api/v1/readings";
    
    http.begin(url);
    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS); // Permite seguir el 307
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", "LLAVE DE ACCESO"); // <-- LLAVE DE SEGURIDAD AGREGADA

    int httpCode = http.POST(payload);

    if (httpCode == 201) {
        Serial.println("✓ Lectura enviada exitosamente");
        String response = http.getString();
        Serial.println("Respuesta: " + response);
    } else {
        Serial.printf("✗ Error HTTP: %d\n", httpCode);
        Serial.println("Payload: " + payload);
    }

    http.end();
}
```
"Codigo esp32 peticiones MQTT"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Arduino.h>

// Aumenta el búfer MQTT para evitar cortes por desbordamiento con TLS
#ifndef MQTT_MAX_PACKET_SIZE
#define MQTT_MAX_PACKET_SIZE 512
#endif

// ===== Configuración de Red =====
const char* SSID = "SSID";
const char* PASSWORD = "PASSWORD";

// ===== Configuración Celda y ADC =====
const int CELL_ID = 1; 
const int ADC_PIN = 2; // GPIO 2 (ADC1_CH2 para ESP32-C6)
const int INTERVAL_MS = 10000; // 10 segundos
const float REF_VOLTAGE = 3.3;
const int ADC_MAX = 4095;

// ===== Configuración HiveMQ Cloud =====
const char* mqtt_server = "Tu MQTT";
const int MQTT_PORT = PUERTO; // CORREGIDO: Puerto 8883 obligatorio para PubSubClient con TLS

const char* MQTT_USER = "tu usuario"; 
const char* MQTT_PASSWORD = "tu contraseña"; 

const char* MQTT_TOPIC = "MQTT";

WiFiClientSecure espClient;
PubSubClient client(espClient);
unsigned long last_send = 0;

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println("\n\nIniciando ESP32-C6 con HiveMQ Cloud...");
    connect_wifi();
    
    espClient.setInsecure(); 
    client.setServer(mqtt_server, MQTT_PORT);
    
    // AGREGA ESTA LÍNEA AQUÍ PARA AMPLIAR EL TIEMPO DE ESPERA A 60 SEGUNDOS:
    client.setKeepAlive(60); 
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connect_wifi();
    }

    if (!client.connected()) {
        reconnect_mqtt();
    }
    client.loop(); // <- Esto debe ejecutarse constantemente sin bloqueos

    if (millis() - last_send > INTERVAL_MS) {
        send_reading_mqtt();
        last_send = millis();
    }
}

void connect_wifi() {
    Serial.printf("Conectando a WiFi: %s\n", SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Conectando a HiveMQ Cloud... ");
        String clientId = "ESP32C6-" + String(random(0xffff), HEX);
        
        // El último número (60) es el Keep-Alive en segundos. Asegura que la sesión no muera rápido.
        if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
            Serial.println("✓ Conectado exitosamente al broker");
            // Importante: re-suscribirse o asegurar el estado si fuera necesario
        } else {
            Serial.printf("✗ Falló, código de error (rc): %d. Reintentando en 5s...\n", client.state());
            delay(5000);
        }
    }
}

void send_reading_mqtt() {
    int raw_adc = analogRead(ADC_PIN);
    float voltage = (raw_adc / (float)ADC_MAX) * REF_VOLTAGE;

    // Calcula el porcentaje de eficiencia basado en tu voltaje de referencia
    float efficiency = (voltage / REF_VOLTAGE) * 100.0;
    if (efficiency > 100.0) efficiency = 100.0; // Límite máximo de seguridad

    Serial.printf("ADC Raw: %d, Voltaje: %.2f V, Eficiencia: %.1f%%\n", raw_adc, voltage, efficiency);

    // Agregamos "efficiency_percentage" al JSON que viaja al broker
    String payload = "{\"cell_id\":" + String(CELL_ID) +
                     ",\"voltage_measured\":" + String(voltage, 2) +
                     ",\"efficiency_percentage\":" + String(efficiency, 2) + "}";

    if (client.publish(MQTT_TOPIC, payload.c_str())) {
        Serial.println("✓ Paquete JSON publicado en HiveMQ");
    } else {
        Serial.println("✗ Error al publicar el mensaje");
    }
}

**Instrucciones:**
1. Instalar Thonny IDE
2. Conectar ESP32
3. Crear nuevo archivo con el código anterior
4. Modificar SSID, PASSWORD, API_URL, CELL_ID
5. Run (Thonny ejecuta en el dispositivo)

---

## Configuración de Sensores

### Divisor de Voltaje (Recomendado para Celdas Fotovoltaicas)

Para leer voltajes > 3.3V:

```
Entrada (0-12V) ──[R1=10kΩ]──┬── Salida (0-3.3V) → A0
                             [R2=3.3kΩ]
                             ─── GND

Voltaje Salida = Voltaje Entrada × (R2 / (R1 + R2))
                = Voltaje Entrada × (3.3 / 13.3)
```

### Sensor Actual (ACS712)

```
Celda ──[ACS712]──
         │
         ├─ OUT → A0 (0-3.3V)
         ├─ +5V → 5V
         └─ GND → GND

Conversión:
- Centro (sin corriente): 2.5V
- Sensibilidad: 185 mV/A
- Rango: ±30A
```

---

## Testing de la Integración

### 1. Verificar Lectura del ADC

```python
# En la terminal serial
import machine

adc = machine.ADC(machine.Pin(36))
for i in range(10):
    print(adc.read())
    time.sleep(0.5)
```

### 2. Verificar Conexión WiFi

```python
import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("SSID", "PASSWORD")
while not wlan.isconnected():
    print(wlan.status())
print(wlan.ifconfig())
```

### 3. Probar POST a API

```bash
# Desde terminal:
curl -X POST http://localhost:8000/api/v1/readings \
  -H "Content-Type: application/json" \
  -d '{"cell_id": 1, "voltage_measured": 4.85}'

# Respuesta esperada (201):
{
  "id": 1,
  "cell_id": 1,
  "voltage_measured": 4.85,
  "efficiency_percentage": 97.0,
  "is_anomaly": false,
  "timestamp": "2026-09-11T...",
  "created_at": "2026-09-11T..."
}
```

---

## Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| ESP32 no se conecta a WiFi | SSID/Password incorrecto | Verificar credenciales WiFi |
| Voltaje siempre 0 | Sensor no conectado | Revisar conexión ADC |
| Error 400 al enviar | Cell ID no existe | Crear celda primero con POST /api/v1/cells |
| Error 404 | API no accesible | Verificar URL y conectividad de red |
| Timeout en HTTP | Red lenta | Aumentar timeout: `http.begin(url, 10000)` |

---

## Mejoras Futuras

- [ ] Agregar batería de respaldo
- [ ] Implementar almacenamiento local si API no está disponible
- [ ] Agregar sensor de temperatura
- [ ] Implementar compresión de datos
- [ ] Agregar autenticación con API Key
