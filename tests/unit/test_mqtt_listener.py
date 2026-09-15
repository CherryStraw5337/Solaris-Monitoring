import json
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
from paho.mqtt.client import CallbackAPIVersion, ConnectFlags, DisconnectFlags
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.reasoncodes import ReasonCode
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from utils import mqtt_listener
from utils.models import PhotovoltaicCell, Reading
from utils.mqtt_listener import (
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_TOPIC,
    MqttConfig,
    MqttListener,
    MqttStatus,
)

BROKER_ENV = {
    "MQTT_HOST": "broker.example.com",
    "MQTT_USERNAME": "device-user",
    "MQTT_PASSWORD": "device-pass",
}

CONNACK_OK = ReasonCode(PacketTypes.CONNACK, "Success")
CONNACK_REFUSED = ReasonCode(PacketTypes.CONNACK, "Not authorized")


def broker_config(**overrides: str) -> MqttConfig:
    config = MqttConfig.from_env({**BROKER_ENV, **overrides})
    assert config is not None
    return config


def unused_session_factory() -> Session:
    raise AssertionError("no se esperaba abrir una sesión")


def message(payload: object, topic: str = DEFAULT_MQTT_TOPIC) -> MagicMock:
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return MagicMock(topic=topic, payload=raw)


# ---------- configuración ----------


def test_mqtt_is_disabled_when_no_broker_is_configured() -> None:
    assert MqttConfig.from_env({}) is None


def test_config_reads_credentials_from_the_environment() -> None:
    assert MqttConfig.from_env(BROKER_ENV) == MqttConfig(
        host="broker.example.com",
        port=DEFAULT_MQTT_PORT,
        username="device-user",
        password="device-pass",
        topic=DEFAULT_MQTT_TOPIC,
    )


def test_config_accepts_custom_port_and_topic() -> None:
    config = broker_config(MQTT_PORT="1883", MQTT_TOPIC="a/b")

    assert (config.port, config.topic) == (1883, "a/b")


@pytest.mark.parametrize("missing", ["MQTT_USERNAME", "MQTT_PASSWORD"])
def test_config_requires_credentials_when_a_host_is_set(missing: str) -> None:
    env = {key: value for key, value in BROKER_ENV.items() if key != missing}

    with pytest.raises(ValueError, match=missing):
        MqttConfig.from_env(env)


def test_module_does_not_embed_broker_credentials() -> None:
    for name in ("MQTT_BROKER", "MQTT_USER", "MQTT_PASSWORD"):
        assert not hasattr(mqtt_listener, name)


# ---------- ciclo de vida ----------


def test_start_without_broker_stays_disabled(mock_mqtt_start: Any) -> None:
    listener = MqttListener(None, unused_session_factory)

    listener.start()

    assert listener.status is MqttStatus.DISABLED
    mock_mqtt_start.assert_not_called()


def test_start_connects_in_background_with_environment_credentials(
    mock_mqtt_start: Any,
) -> None:
    listener = MqttListener(broker_config(), unused_session_factory)

    listener.start()

    client = mock_mqtt_start.return_value
    assert mock_mqtt_start.call_args.kwargs["callback_api_version"] is CallbackAPIVersion.VERSION2
    client.username_pw_set.assert_called_once_with("device-user", "device-pass")
    client.tls_set.assert_called_once_with()
    # connect_async no bloquea el arranque y paho reintenta si el broker no responde.
    client.connect_async.assert_called_once_with("broker.example.com", DEFAULT_MQTT_PORT, 60)
    client.loop_start.assert_called_once_with()
    assert listener.status is MqttStatus.CONNECTING


def test_start_survives_a_client_error(mock_mqtt_start: Any) -> None:
    mock_mqtt_start.return_value.connect_async.side_effect = OSError("sin red")
    listener = MqttListener(broker_config(), unused_session_factory)

    listener.start()

    assert listener.status is MqttStatus.DISCONNECTED


def test_stop_disconnects_and_stops_the_network_loop(mock_mqtt_start: Any) -> None:
    listener = MqttListener(broker_config(), unused_session_factory)
    listener.start()

    listener.stop()

    client = mock_mqtt_start.return_value
    client.disconnect.assert_called_once_with()
    client.loop_stop.assert_called_once_with()
    assert listener.status is MqttStatus.DISCONNECTED


def test_stop_without_a_client_is_a_no_op() -> None:
    listener = MqttListener(None, unused_session_factory)

    listener.stop()

    assert listener.status is MqttStatus.DISABLED


# ---------- callbacks de conexión (firma VERSION2: 5 argumentos) ----------


def test_on_connect_subscribes_with_qos_1() -> None:
    client = MagicMock()
    listener = MqttListener(broker_config(MQTT_TOPIC="solaris/test"), unused_session_factory)

    listener.on_connect(client, None, ConnectFlags(session_present=False), CONNACK_OK, None)

    client.subscribe.assert_called_once_with("solaris/test", qos=1)
    assert listener.status is MqttStatus.CONNECTED


def test_on_connect_does_not_subscribe_when_the_broker_rejects() -> None:
    client = MagicMock()
    listener = MqttListener(broker_config(), unused_session_factory)

    listener.on_connect(client, None, ConnectFlags(session_present=False), CONNACK_REFUSED, None)

    client.subscribe.assert_not_called()
    assert listener.status is MqttStatus.DISCONNECTED


@pytest.mark.parametrize(
    ("reason", "level"),
    [
        (ReasonCode(PacketTypes.DISCONNECT, "Normal disconnection"), logging.INFO),
        (ReasonCode(PacketTypes.DISCONNECT, "Unspecified error"), logging.WARNING),
    ],
)
def test_on_disconnect_marks_the_listener_as_disconnected(
    reason: ReasonCode, level: int, caplog: pytest.LogCaptureFixture
) -> None:
    listener = MqttListener(broker_config(), unused_session_factory)
    listener.status = MqttStatus.CONNECTED

    with caplog.at_level(logging.INFO):
        listener.on_disconnect(
            MagicMock(), None, DisconnectFlags(is_disconnect_packet_from_server=False), reason, None
        )

    assert listener.status is MqttStatus.DISCONNECTED
    assert [record.levelno for record in caplog.records] == [level]


# ---------- ingesta ----------


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def cell(session_factory: sessionmaker[Session]) -> PhotovoltaicCell:
    with session_factory() as session:
        stored = PhotovoltaicCell(
            name="Celda_01",
            location="Techo",
            rated_voltage=5.0,
            max_safe_voltage=6.0,
            efficiency_threshold=80.0,
            is_active=True,
        )
        session.add(stored)
        session.commit()
        session.refresh(stored)
        session.expunge(stored)
        return stored


def stored_readings(session_factory: sessionmaker[Session]) -> list[Reading]:
    with session_factory() as session:
        return list(session.scalars(select(Reading)))


def test_message_is_ingested_through_the_domain_rules(
    session_factory: sessionmaker[Session], cell: PhotovoltaicCell
) -> None:
    listener = MqttListener(broker_config(), session_factory)

    # El firmware también envía efficiency_percentage calculada contra 3.3 V: se ignora.
    listener.on_message(
        MagicMock(),
        None,
        message({"cell_id": cell.id, "voltage_measured": 4.85, "efficiency_percentage": 100.0}),
    )

    [reading] = stored_readings(session_factory)
    assert reading.efficiency_percentage == 97.0
    assert reading.is_anomaly is False


def test_several_cells_share_the_same_topic(
    session_factory: sessionmaker[Session], cell: PhotovoltaicCell
) -> None:
    with session_factory() as session:
        other = PhotovoltaicCell(
            name="Celda_02",
            location="Patio",
            rated_voltage=10.0,
            max_safe_voltage=12.0,
            efficiency_threshold=80.0,
            is_active=True,
        )
        session.add(other)
        session.commit()
        other_id = other.id
    listener = MqttListener(broker_config(), session_factory)

    for cell_id in (cell.id, other_id):
        listener.on_message(
            MagicMock(), None, message({"cell_id": cell_id, "voltage_measured": 5.0})
        )

    by_cell = {r.cell_id: r.efficiency_percentage for r in stored_readings(session_factory)}
    # Cada lectura usa el voltaje nominal de su propia celda.
    assert by_cell == {cell.id: 100.0, other_id: 50.0}


def test_message_over_the_safe_voltage_is_flagged_as_anomaly(
    session_factory: sessionmaker[Session], cell: PhotovoltaicCell
) -> None:
    listener = MqttListener(broker_config(), session_factory)

    listener.on_message(MagicMock(), None, message({"cell_id": cell.id, "voltage_measured": 7.0}))

    [reading] = stored_readings(session_factory)
    assert reading.is_anomaly is True


@pytest.mark.parametrize(
    "payload",
    [
        b"no es json",
        b"\xff\xfe",
        {"voltage_measured": 4.8},
        {"cell_id": 1, "voltage_measured": 0},
        {"cell_id": 1, "voltage_measured": 4.8, "timestamp": "2999-01-01T00:00:00Z"},
    ],
)
def test_invalid_payloads_are_discarded_without_touching_the_database(
    payload: object, caplog: pytest.LogCaptureFixture
) -> None:
    listener = MqttListener(broker_config(), unused_session_factory)

    with caplog.at_level(logging.WARNING):
        listener.on_message(MagicMock(), None, message(payload))

    assert "descartada" in caplog.text


def test_unknown_cell_is_discarded(
    session_factory: sessionmaker[Session], caplog: pytest.LogCaptureFixture
) -> None:
    listener = MqttListener(broker_config(), session_factory)

    with caplog.at_level(logging.WARNING):
        listener.on_message(MagicMock(), None, message({"cell_id": 99, "voltage_measured": 4.8}))

    assert stored_readings(session_factory) == []
    assert "99" in caplog.text


def test_inactive_cell_is_discarded(
    session_factory: sessionmaker[Session], cell: PhotovoltaicCell
) -> None:
    with session_factory() as session:
        session.get_one(PhotovoltaicCell, cell.id).is_active = False
        session.commit()
    listener = MqttListener(broker_config(), session_factory)

    listener.on_message(MagicMock(), None, message({"cell_id": cell.id, "voltage_measured": 4.8}))

    assert stored_readings(session_factory) == []


def test_a_database_that_cannot_open_does_not_stop_the_listener(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def broken_factory() -> Session:
        raise RuntimeError("BD caída")

    listener = MqttListener(broker_config(), broken_factory)

    with caplog.at_level(logging.ERROR):
        listener.on_message(MagicMock(), None, message({"cell_id": 1, "voltage_measured": 4.8}))

    assert "BD caída" in caplog.text


def test_an_unexpected_error_rolls_back_and_closes_the_session() -> None:
    session = MagicMock()
    session.get.side_effect = RuntimeError("fallo inesperado")
    listener = MqttListener(broker_config(), lambda: session)

    listener.on_message(MagicMock(), None, message({"cell_id": 1, "voltage_measured": 4.8}))

    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
