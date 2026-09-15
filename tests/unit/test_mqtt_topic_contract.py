import re
from pathlib import Path

from utils.mqtt_listener import DEFAULT_MQTT_TOPIC

REPO_ROOT = Path(__file__).resolve().parents[2]
FIRMWARE_DIR = REPO_ROOT / "src" / "firmware" / "esp32"


def test_default_topic_is_shared_by_every_cell() -> None:
    # Varias celdas publican en el mismo topic; la celda la identifica cell_id en el JSON.
    assert DEFAULT_MQTT_TOPIC == "solaris/readings"
    assert not re.search(r"cell_?\d", DEFAULT_MQTT_TOPIC)


def test_render_blueprint_uses_the_default_topic() -> None:
    blueprint = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")

    match = re.search(r"key: MQTT_TOPIC\s+value: (\S+)", blueprint)

    assert match is not None
    assert match.group(1) == DEFAULT_MQTT_TOPIC


def test_firmware_publishes_to_the_default_topic() -> None:
    sketch = (FIRMWARE_DIR / "MQTT.ino").read_text(encoding="utf-8")

    match = re.search(r'MQTT_TOPIC\s*=\s*"([^"]+)"', sketch)

    assert match is not None
    assert match.group(1) == DEFAULT_MQTT_TOPIC


def test_each_board_sets_its_cell_id_in_secrets() -> None:
    sketch = (FIRMWARE_DIR / "MQTT.ino").read_text(encoding="utf-8")
    example = (FIRMWARE_DIR / "secrets.example.h").read_text(encoding="utf-8")

    assert "const int CELL_ID" not in sketch
    assert re.search(r"#define\s+CELL_ID\s+\d+", example)
