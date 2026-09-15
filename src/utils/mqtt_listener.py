from __future__ import annotations

import logging
import os
import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import paho.mqtt.client as mqtt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from utils.dependencies import get_reading_service
from utils.domain.errors import DomainError
from utils.schemas.reading import ReadingCreate

logger = logging.getLogger(__name__)

DEFAULT_MQTT_PORT = 8883
DEFAULT_MQTT_TOPIC = "solaris/readings"
KEEPALIVE_SECONDS = 60


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


class MqttStatus(StrEnum):
    DISABLED = "disabled"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class MqttListener:
    """Adaptador de entrada MQTT: aplica las mismas reglas que POST /api/v1/readings."""

    def __init__(self, config: MqttConfig | None, session_factory: Callable[[], Session]) -> None:
        self._config = config
        self._session_factory = session_factory
        self._client: Any = None
        self.status = MqttStatus.DISABLED

    def start(self) -> None:
        if self._config is None:
            logger.info("MQTT deshabilitado: MQTT_HOST no está definido")
            return

        try:
            client = mqtt.Client(
                client_id=f"FastAPI-Subscriber-{random.randint(0, 0xFFFF)}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )
            client.username_pw_set(self._config.username, self._config.password)
            client.tls_set()
            client.on_connect = self.on_connect
            client.on_disconnect = self.on_disconnect
            client.on_message = self.on_message
            # connect_async + loop_start no bloquean el arranque de la API y paho
            # reintenta la conexión en su propio hilo si el broker no responde.
            client.connect_async(self._config.host, self._config.port, KEEPALIVE_SECONDS)
            client.loop_start()
        except Exception:
            logger.exception("No se pudo iniciar el cliente MQTT")
            self.status = MqttStatus.DISCONNECTED
            return

        self._client = client
        self.status = MqttStatus.CONNECTING
        logger.info("Conectando al broker MQTT %s:%s", self._config.host, self._config.port)

    def stop(self) -> None:
        if self._client is None:
            return
        self._client.disconnect()
        self._client.loop_stop()
        self._client = None
        self.status = MqttStatus.DISCONNECTED
        logger.info("Cliente MQTT desconectado")

    # Firmas de CallbackAPIVersion.VERSION2: paho pasa 5 argumentos a on_connect/on_disconnect.
    def on_connect(
        self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any
    ) -> None:
        if reason_code.is_failure:
            self.status = MqttStatus.DISCONNECTED
            logger.error("El broker MQTT rechazó la conexión: %s", reason_code)
            return
        assert self._config is not None
        client.subscribe(self._config.topic, qos=1)
        self.status = MqttStatus.CONNECTED
        logger.info("Conectado al broker MQTT; suscrito a %s", self._config.topic)

    def on_disconnect(
        self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any
    ) -> None:
        self.status = MqttStatus.DISCONNECTED
        level = logging.WARNING if reason_code.is_failure else logging.INFO
        logger.log(level, "Desconectado del broker MQTT: %s", reason_code)

    def on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        try:
            payload = ReadingCreate.model_validate_json(msg.payload)
        except ValidationError as exc:
            logger.warning(
                "Lectura MQTT descartada en %s: payload inválido (%s)",
                msg.topic,
                exc.errors(include_url=False, include_input=False),
            )
            return

        try:
            session = self._session_factory()
        except Exception:
            logger.exception("Lectura MQTT descartada: no se pudo abrir la base de datos")
            return

        # Cualquier excepción que escape de este callback detendría el hilo de red de paho.
        try:
            reading = get_reading_service(session).create(payload)
        except DomainError as exc:
            logger.warning("Lectura MQTT descartada: %s", exc)
        except Exception:
            session.rollback()
            logger.exception("Error inesperado al guardar la lectura MQTT")
        else:
            logger.info(
                "Lectura MQTT guardada: celda %s, %s V, %s %%, anomalía=%s",
                reading.cell_id,
                reading.voltage_measured,
                reading.efficiency_percentage,
                reading.is_anomaly,
            )
        finally:
            session.close()
