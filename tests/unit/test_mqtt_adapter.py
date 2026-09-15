"""Tests for MQTT adapter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.config import Settings
from utils.mqtt_adapter import MQTTAdapter
from utils.schemas.reading import ReadingCreate


@pytest.fixture
def mqtt_settings() -> Settings:
    """Settings with MQTT enabled."""
    return Settings(
        mqtt_host="test.hivemq.cloud",
        mqtt_port=8883,
        mqtt_username="testuser",
        mqtt_password="testpass",
        mqtt_topic="solaris/cells/+/readings",
    )


@pytest.fixture
def mqtt_settings_disabled() -> Settings:
    """Settings with MQTT disabled."""
    return Settings()


@pytest.fixture
def mock_db_factory():
    """Mock database session factory."""
    mock_session = MagicMock()
    return Mock(return_value=mock_session)


class TestMQTTAdapter:
    """Test MQTT adapter initialization and status."""

    def test_mqtt_adapter_enabled_with_host(self, mqtt_settings, mock_db_factory):
        """MQTT adapter is enabled when MQTT_HOST is configured."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        assert adapter.enabled is True
        assert adapter.status == "disabled"  # Initial status

    def test_mqtt_adapter_disabled_without_host(self, mqtt_settings_disabled, mock_db_factory):
        """MQTT adapter is disabled when MQTT_HOST is not configured."""
        adapter = MQTTAdapter(mqtt_settings_disabled, mock_db_factory)
        assert adapter.enabled is False
        assert adapter.status == "disabled"

    def test_extract_cell_id_from_valid_topic(self, mqtt_settings, mock_db_factory):
        """Extract cell_id from valid topic format."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        cell_id = adapter._extract_cell_id_from_topic("solaris/cells/123/readings")
        assert cell_id == "123"

    def test_extract_cell_id_from_invalid_topic(self, mqtt_settings, mock_db_factory):
        """Return None for invalid topic format."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        assert adapter._extract_cell_id_from_topic("invalid/topic") is None
        assert adapter._extract_cell_id_from_topic("solaris/invalid/123/readings") is None

    def test_on_connect_success(self, mqtt_settings, mock_db_factory):
        """On connect callback sets status to connected and subscribes."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        mock_client = MagicMock()
        
        adapter._on_connect(mock_client, None, {}, 0)
        
        assert adapter.status == "connected"
        mock_client.subscribe.assert_called_once_with(mqtt_settings.mqtt_topic, qos=1)

    def test_on_connect_failure(self, mqtt_settings, mock_db_factory):
        """On connect callback sets status to disconnected on failure."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        mock_client = MagicMock()
        
        adapter._on_connect(mock_client, None, {}, 1)  # Non-zero rc means error
        
        assert adapter.status == "disconnected"

    def test_on_disconnect(self, mqtt_settings, mock_db_factory):
        """On disconnect callback sets status."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        mock_client = MagicMock()
        
        adapter._on_disconnect(mock_client, None, 0)
        assert adapter.status == "disconnected"


class TestMQTTMessageHandling:
    """Test MQTT message validation and ingestion."""

    def test_on_message_with_valid_payload(self, mqtt_settings, mock_db_factory):
        """Valid JSON payload creates reading."""
        mock_session = mock_db_factory()
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        
        with patch("utils.mqtt_adapter.ReadingService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Create a mock MQTT message
            mock_msg = MagicMock()
            mock_msg.topic = "solaris/cells/1/readings"
            mock_msg.payload = json.dumps({
                "voltage_measured": 4.85,
                "timestamp": "2026-09-14T10:00:00Z"
            }).encode("utf-8")
            
            adapter._on_message(MagicMock(), None, mock_msg)
            
            # Verify ReadingService.create was called
            mock_service.create.assert_called_once()

    def test_on_message_with_invalid_json(self, mqtt_settings, mock_db_factory):
        """Invalid JSON payload is logged and ignored."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        
        mock_msg = MagicMock()
        mock_msg.topic = "solaris/cells/1/readings"
        mock_msg.payload = b"{ invalid json }"
        
        with patch("utils.mqtt_adapter.logger") as mock_logger:
            adapter._on_message(MagicMock(), None, mock_msg)
            mock_logger.warning.assert_called()

    def test_on_message_with_invalid_topic(self, mqtt_settings, mock_db_factory):
        """Invalid topic format is logged and ignored."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        
        mock_msg = MagicMock()
        mock_msg.topic = "invalid/topic/format"
        mock_msg.payload = json.dumps({"voltage_measured": 4.85}).encode("utf-8")
        
        with patch("utils.mqtt_adapter.logger") as mock_logger:
            adapter._on_message(MagicMock(), None, mock_msg)
            mock_logger.warning.assert_called()

    def test_on_message_with_missing_required_field(self, mqtt_settings, mock_db_factory):
        """Missing required field in payload is logged and ignored."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        
        mock_msg = MagicMock()
        mock_msg.topic = "solaris/cells/1/readings"
        mock_msg.payload = json.dumps({
            "timestamp": "2026-09-14T10:00:00Z"
            # Missing voltage_measured
        }).encode("utf-8")
        
        with patch("utils.mqtt_adapter.logger") as mock_logger:
            adapter._on_message(MagicMock(), None, mock_msg)
            mock_logger.warning.assert_called()

    def test_get_status(self, mqtt_settings, mock_db_factory):
        """Get current MQTT status."""
        adapter = MQTTAdapter(mqtt_settings, mock_db_factory)
        assert adapter.get_status() == "disabled"
        
        adapter.status = "connected"
        assert adapter.get_status() == "connected"
