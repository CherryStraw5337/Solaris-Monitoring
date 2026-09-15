"""MQTT adapter for IoT device reading ingestion (HiveMQ Cloud via paho-mqtt)."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Callable

import paho.mqtt.client as mqtt

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from utils.config import Settings
from utils.dependencies import build_reading_analyzer
from utils.repositories.cell_repo import SqlAlchemyCellRepository
from utils.repositories.reading_repo import SqlAlchemyReadingRepository
from utils.schemas.reading import ReadingCreate
from utils.services.reading_service import ReadingService

logger = logging.getLogger(__name__)


class MQTTAdapter:
    """MQTT client adapter for Solaris Monitoring IoT readings ingestion."""

    def __init__(self, settings: Settings, db_session_factory: Callable[[], Session]):
        """Initialize MQTT adapter with settings and database session factory.

        Args:
            settings: FastAPI Settings with MQTT configuration
            db_session_factory: Callable that returns a new database session
        """
        self.settings = settings
        self.db_session_factory = db_session_factory
        self.client: mqtt.Client | None = None
        self.status = "disabled"  # disabled, connecting, connected, disconnected
        self.enabled = bool(settings.mqtt_host)

    def _extract_cell_id_from_topic(self, topic: str) -> str | None:
        """Extract cell_id from topic path solaris/cells/{cell_id}/readings.

        Args:
            topic: MQTT topic string

        Returns:
            Extracted cell_id or None if topic format is invalid
        """
        parts = topic.split("/")
        if len(parts) >= 3 and parts[0] == "solaris" and parts[1] == "cells":
            return parts[2]
        return None

    def _on_connect(
        self, client: mqtt.Client, userdata: None, flags: dict, rc: int
    ) -> None:
        """Callback for MQTT connection events."""
        if rc == 0:
            logger.info(
                "MQTT connected successfully. Subscribing to topic %s",
                self.settings.mqtt_topic,
            )
            self.status = "connected"
            client.subscribe(self.settings.mqtt_topic, qos=1)
        else:
            logger.error("MQTT connection failed with code %d", rc)
            self.status = "disconnected"

    def _on_disconnect(self, client: mqtt.Client, userdata: None, rc: int) -> None:
        """Callback for MQTT disconnection events."""
        if rc == 0:
            logger.info("MQTT disconnected cleanly")
        else:
            logger.warning("MQTT disconnected with code %d", rc)
        self.status = "disconnected"

    def _on_message(
        self, client: mqtt.Client, userdata: None, msg: mqtt.MQTTMessage
    ) -> None:
        """Callback for MQTT message reception. Validates and ingests readings.

        Args:
            client: MQTT client
            userdata: User data (unused)
            msg: MQTT message object
        """
        topic = msg.topic
        payload_bytes = msg.payload

        # Extract cell_id from topic
        cell_id_str = self._extract_cell_id_from_topic(topic)
        if not cell_id_str:
            logger.warning(
                "Invalid topic format: %s. Expected solaris/cells/{cell_id}/readings",
                topic,
            )
            return

        # Parse JSON payload
        try:
            payload_dict = json.loads(payload_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Invalid JSON payload on topic %s: %s", topic, e)
            return

        # Validate with ReadingCreate schema
        try:
            reading_data = ReadingCreate(**payload_dict, cell_id=int(cell_id_str))
        except (ValueError, TypeError) as e:
            logger.warning("Invalid reading data on topic %s: %s", topic, e)
            return

        # Ingest reading into database
        try:
            db = self.db_session_factory()
            reading_repo = SqlAlchemyReadingRepository(db)
            cell_repo = SqlAlchemyCellRepository(db)
            analyzer = build_reading_analyzer()
            service = ReadingService(readings=reading_repo, cells=cell_repo, analyzer=analyzer)
            service.create(reading_data)
            logger.info(
                "Reading ingested from MQTT topic %s for cell_id %s", topic, cell_id_str
            )
        except Exception as e:
            logger.error("Error ingesting reading from MQTT topic %s: %s", topic, e)
        finally:
            db.close()

    def connect(self) -> None:
        """Connect to MQTT broker (blocking, runs in thread or executor)."""
        if not self.enabled:
            logger.info("MQTT adapter disabled (MQTT_HOST not configured)")
            self.status = "disabled"
            return

        # Type narrowing: if enabled is True, mqtt_host must be set
        assert self.settings.mqtt_host is not None, "mqtt_host must be set if adapter is enabled"

        logger.info(
            "Connecting to MQTT broker %s:%d",
            self.settings.mqtt_host,
            self.settings.mqtt_port,
        )
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Set username and password if provided
        if self.settings.mqtt_username and self.settings.mqtt_password:
            self.client.username_pw_set(
                self.settings.mqtt_username, self.settings.mqtt_password
            )

        # Enable TLS for secure connection to HiveMQ Cloud
        self.client.tls_set()
        self.client._tls_insecure = False

        try:
            self.client.connect(
                self.settings.mqtt_host, self.settings.mqtt_port, keepalive=60
            )
            self.status = "connecting"
            # Start the network loop (blocking until disconnect)
            self.client.loop_forever()
        except Exception as e:
            logger.error("Failed to connect to MQTT broker: %s", e)
            self.status = "disconnected"

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client:
            logger.info("Disconnecting from MQTT broker")
            self.client.disconnect()
            self.client.loop_stop()
            self.status = "disconnected"

    def get_status(self) -> str:
        """Get current MQTT connection status.

        Returns:
            Status string: 'disabled', 'connecting', 'connected', or 'disconnected'
        """
        return self.status
