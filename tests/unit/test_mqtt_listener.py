from typing import Any
from unittest.mock import MagicMock

import pytest

from utils import mqtt_listener
from utils.mqtt_listener import DEFAULT_MQTT_PORT, DEFAULT_MQTT_TOPIC, MqttConfig, iniciar_mqtt

BROKER_ENV = {
    "MQTT_HOST": "broker.example.com",
    "MQTT_USERNAME": "device-user",
    "MQTT_PASSWORD": "device-pass",
}


def broker_config(**overrides: str) -> MqttConfig:
    config = MqttConfig.from_env({**BROKER_ENV, **overrides})
    assert config is not None
    return config


def test_mqtt_is_disabled_when_no_broker_is_configured() -> None:
    assert MqttConfig.from_env({}) is None


def test_config_reads_credentials_from_the_environment() -> None:
    config = MqttConfig.from_env(BROKER_ENV)

    assert config == MqttConfig(
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


def test_start_without_broker_does_not_create_a_client(mock_mqtt_start: Any) -> None:
    assert iniciar_mqtt({}) is None
    mock_mqtt_start.assert_not_called()


def test_start_connects_with_environment_credentials(mock_mqtt_start: Any) -> None:
    client = iniciar_mqtt(BROKER_ENV)

    instance = mock_mqtt_start.return_value
    assert client is instance
    instance.username_pw_set.assert_called_once_with("device-user", "device-pass")
    instance.tls_set.assert_called_once_with()
    instance.connect.assert_called_once_with("broker.example.com", DEFAULT_MQTT_PORT, 60)
    instance.loop_start.assert_called_once_with()


def test_start_survives_an_unreachable_broker(mock_mqtt_start: Any) -> None:
    mock_mqtt_start.return_value.connect.side_effect = OSError("sin red")

    assert iniciar_mqtt(BROKER_ENV) is None


def test_on_connect_subscribes_to_the_configured_topic() -> None:
    client = MagicMock()
    config = broker_config(MQTT_TOPIC="solaris/test")

    # paho con CallbackAPIVersion.VERSION2 invoca on_connect con 5 argumentos.
    mqtt_listener.on_connect(client, config, None, 0, None)

    client.subscribe.assert_called_once_with("solaris/test")


def test_on_connect_does_not_subscribe_when_the_broker_rejects() -> None:
    client = MagicMock()

    mqtt_listener.on_connect(client, broker_config(), None, 5, None)

    client.subscribe.assert_not_called()
