#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "secrets.h"  // Carga tus credenciales locales

const int CELL_ID = 1;
const int ADC_PIN = 34;       // Pin analógico donde entra el voltaje de la celda
const float REF_VOLTAGE = 3.3; // Voltaje de referencia del ESP32
const int ADC_MAX = 4095;     // Resolución de 12 bits del ESP32

WiFiClientSecure espClient;
PubSubClient client(espClient);

const char* MQTT_TOPIC = "solaris/edsia_beyond/cell_1/voltage";

void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Conectando a Wi-Fi: ");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nWiFi conectado exitosamente");
}

void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Intentando conexión MQTT...");
        String clientId = "ESP32Client-" + String(random(0xffff), HEX);
        
        if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
            Serial.println(" conectado!");
        } else {
            Serial.print(" falló, rc=");
            Serial.print(client.state());
            Serial.println(" reintentando en 5 segundos...");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    setup_wifi();

    // Configurar TLS para HiveMQ Cloud (puerto 8883)
    espClient.setInsecure(); // Omitir validación estricta de certificado para pruebas rápidas
    client.setServer(MQTT_BROKER, 8883);
}

void loop() {
    if (!client.connected()) {
        reconnect_mqtt();
    }
    client.loop();

    // Lectura del sensor y cálculo de divisor / eficiencia
    int raw_adc = analogRead(ADC_PIN);
    float voltage = (raw_adc / (float)ADC_MAX) * REF_VOLTAGE;

    // Supongamos un factor de divisor de voltaje si usas resistencias (ejemplo: multiplicador x2)
    voltage = voltage * 2.0; 

    float efficiency = (voltage / 3.3) * 100.0; // Ajusta según el voltaje máximo de tu celda
    if (efficiency > 100.0) efficiency = 100.0;

    // Crear paquete JSON
    String payload = "{\"cell_id\":" + String(CELL_ID) +
                     ",\"voltage_measured\":" + String(voltage, 2) +
                     ",\"efficiency_percentage\":" + String(efficiency, 2) + "}";

    if (client.publish(MQTT_TOPIC, payload.c_str())) {
        Serial.println("✓ Publicado: " + payload);
    } else {
        Serial.println("✗ Error al publicar");
    }

    delay(10000); // Enviar cada 10 segundos
}