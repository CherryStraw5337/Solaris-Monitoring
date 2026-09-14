import json
import time
import paho.mqtt.client as mqtt

MQTT_BROKER = "77bc782066404afd905e5dba6d27d880.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "test"
MQTT_PASSWORD = "13422004"
MQTT_TOPIC = "solaris/edsia_beyond/cell_1/voltage"

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(">>> [TEST] Conectado al broker con éxito. Suscribiendo al topic...")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f">>> [TEST] Error de conexión, código: {reason_code}")

def on_message(client, userdata, msg):
    print(f">>> [TEST] ¡MENSAJE RECIBIDO!: {msg.payload.decode('utf-8')}")

# Inicializar cliente con API v2
client = mqtt.Client(client_id="TestSubscriberScript", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set()

client.on_connect = on_connect
client.on_message = on_message

print(">>> [TEST] Conectando a HiveMQ Cloud...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Bloquear el script con un loop continuo para escuchar en tiempo real
client.loop_forever()