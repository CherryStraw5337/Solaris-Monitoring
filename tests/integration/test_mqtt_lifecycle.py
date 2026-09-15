import warnings
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import Base
from main import create_app
from utils.mqtt_listener import MqttListener, MqttStatus

BROKER_ENV = {
    "MQTT_HOST": "broker.example.com",
    "MQTT_USERNAME": "device-user",
    "MQTT_PASSWORD": "device-pass",
}


@pytest.fixture
def no_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in BROKER_ENV:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def with_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in BROKER_ENV.items():
        monkeypatch.setenv(key, value)


def test_health_reports_mqtt_disabled_without_broker(client: TestClient, no_broker: None) -> None:
    assert client.get("/health").json()["mqtt_status"] == "disabled"


def test_health_reports_the_listener_status(client: TestClient, app: FastAPI) -> None:
    listener: MqttListener = app.state.mqtt
    listener.status = MqttStatus.CONNECTED

    assert client.get("/health").json()["mqtt_status"] == "connected"


def test_health_works_when_the_lifespan_did_not_run(app: FastAPI) -> None:
    # Sin "with", TestClient no ejecuta el lifespan y app.state.mqtt no existe.
    assert TestClient(app).get("/health").json()["mqtt_status"] == "disabled"


def test_lifespan_starts_and_stops_the_listener(with_broker: None, mock_mqtt_start: Any) -> None:
    app = create_app()

    with TestClient(app):
        assert app.state.mqtt.status is MqttStatus.CONNECTING
        mock_mqtt_start.return_value.loop_start.assert_called_once_with()

    mock_mqtt_start.return_value.disconnect.assert_called_once_with()
    mock_mqtt_start.return_value.loop_stop.assert_called_once_with()


def test_startup_leaves_the_schema_to_alembic(no_broker: None) -> None:
    with patch.object(Base.metadata, "create_all") as create_all, TestClient(create_app()):
        pass

    create_all.assert_not_called()


def test_startup_does_not_use_the_deprecated_on_event(no_broker: None) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with TestClient(create_app()) as client:
            assert client.get("/health").status_code == 200
