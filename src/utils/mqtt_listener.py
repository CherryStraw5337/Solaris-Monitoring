from __future__ import annotations

import json
import os
import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from db import SessionLocal  # Importa tu sesión de base de datos
from utils.models import Reading  # Importante para instanciar el objeto de lectura
from utils.repositories.reading_repo import SqlAlchemyReadingRepository

DEFAULT_MQTT_PORT = 8883
DEFAULT_MQTT_TOPIC = "solaris/edsia_beyond/cell_1/voltage"


@dataclass(frozen=True, slots=True)
class MqttConfig:
    host: str
    port: int
    username: str
    password: str
    topic: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> MqttConfig | None:
        source: Mapping[str, str] = os.environ if env is None else env
        host = source.get("MQTT_HOST")
        if not host:
            return None
        missing = [key for key in ("MQTT_USERNAME", "MQTT_PASSWORD") if not source.get(key)]
        if missing:
            raise ValueError(f"MQTT_HOST está definido pero faltan: {', '.join(missing)}")
        return cls(
            host=host,
            port=int(source.get("MQTT_PORT", DEFAULT_MQTT_PORT)),
            username=source["MQTT_USERNAME"],
            password=source["MQTT_PASSWORD"],
            topic=source.get("MQTT_TOPIC", DEFAULT_MQTT_TOPIC),
        )


def on_connect(
    client: Any, userdata: MqttConfig, flags: Any, reason_code: Any, properties: Any = None
) -> None:
    if reason_code == 0:
        print("Conectado exitosamente al broker MQTT desde FastAPI")
        client.subscribe(userdata.topic)
    else:
        print(f"Error de conexión MQTT, código: {reason_code}")


def on_message(client: Any, userdata: Any, msg: Any) -> None:
    try:
        # 1. Decodificar el JSON que manda el ESP32
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)

        cell_id = data.get("cell_id")
        voltage = data.get("voltage_measured")

        # Respaldo automático de eficiencia si el ESP32 no la manda todavía
        efficiency = data.get("efficiency_percentage")
        if efficiency is None:
            max_voltage = 3.3
            efficiency = (
                round((voltage / max_voltage) * 100, 2) if voltage <= max_voltage else 100.0
            )

        print(
            f"Mensaje MQTT recibido -> Celda: {cell_id}, "
            f"Voltaje: {voltage}V, Eficiencia: {efficiency}%"
        )

        # 2. Abrir una sesión de base de datos e insertar la lectura
        db: Session = SessionLocal()
        try:
            reading_repo = SqlAlchemyReadingRepository(db)

            nueva_lectura = Reading(
                cell_id=cell_id, voltage_measured=voltage, efficiency_percentage=efficiency
            )
            reading_repo.add(nueva_lectura)

            print("✓ Lectura guardada en la base de datos exitosamente")
        except Exception as e:
            db.rollback()
            print(f"✗ Error al guardar en BD: {e}")
        finally:
            db.close()

    except Exception as e:
        print(f"Error procesando el mensaje MQTT: {e}")


def iniciar_mqtt(env: Mapping[str, str] | None = None) -> Any:
    config = MqttConfig.from_env(env)
    if config is None:
        # Sin broker configurado la API sigue funcionando: HTTP es el canal principal.
        print("MQTT deshabilitado: MQTT_HOST no está definido")
        return None

    try:
        # Generar un ID único para el cliente de Python para evitar bloqueos del broker
        client_id = "FastAPI-Subscriber-" + str(random.randint(0, 0xFFFF))

        client = mqtt.Client(
            client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        client.username_pw_set(config.username, config.password)

        # Configurar TLS obligatorio para HiveMQ Cloud
        client.tls_set()

        client.user_data_set(config)
        client.on_connect = on_connect
        client.on_message = on_message

        print(f"Intentando conectar al broker MQTT ({config.host}:{config.port})...")

        client.connect(config.host, config.port, 60)
        client.loop_start()
        return client
    except Exception as e:
        print(f"✗ Error crítico al iniciar el cliente MQTT: {e}")
        return None
