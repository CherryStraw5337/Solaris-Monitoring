"""Suscriptor manual para depurar el broker. Uso: definir MQTT_HOST, MQTT_USERNAME y
MQTT_PASSWORD en el entorno y ejecutar `python tests/subscriber_manual.py`."""

import sys
from typing import Any

import paho.mqtt.client as mqtt

sys.path.insert(0, "src")

from utils.mqtt_listener import MqttConfig  # noqa: E402

_loaded = MqttConfig.from_env()
if _loaded is None:
    raise SystemExit("Define MQTT_HOST, MQTT_USERNAME y MQTT_PASSWORD en el entorno.")
config: MqttConfig = _loaded


def on_connect(
    client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None
) -> None:
    if reason_code == 0:
        print(f">>> [TEST] Conectado al broker. Suscribiendo a {config.topic}...")
        client.subscribe(config.topic)
    else:
        print(f">>> [TEST] El broker rechazó la conexión: {reason_code}")


def on_message(client: Any, userdata: Any, msg: Any) -> None:
    print(f">>> [TEST] ¡MENSAJE RECIBIDO!: {msg.payload.decode('utf-8')}")


client = mqtt.Client(
    client_id="TestSubscriberScript", callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set(config.username, config.password)
client.tls_set()

client.on_connect = on_connect
client.on_message = on_message

print(f">>> [TEST] Conectando a {config.host}:{config.port}...")
client.connect(config.host, config.port, 60)

client.loop_forever()
