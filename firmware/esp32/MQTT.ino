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
const char* mqtt_server = "YOUR TOPIC";
const int MQTT_PORT = 8883; // CORREGIDO: Puerto 8883 obligatorio para PubSubClient con TLS

const char* MQTT_USER = "MQTT"; 
const char* MQTT_PASSWORD = "PASSWORD"; 

const char* MQTT_TOPIC = "solaris/edsia_beyond/cell_1/voltage";

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