from fastapi.testclient import TestClient

from edsia_beyond.config import Settings
from edsia_beyond.main import create_app


def test_root_identifies_the_api(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "EDSIA Beyond" in response.json()["message"]


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_schema_is_served(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/api/v1/cells" in schema["paths"]
    assert "/api/v1/readings" in schema["paths"]


def test_app_metadata_comes_from_settings() -> None:
    app = create_app(Settings.from_env({"API_TITLE": "Custom API", "API_VERSION": "9.9.9"}))

    assert app.title == "Custom API"
    assert app.version == "9.9.9"


def test_app_falls_back_to_environment_settings() -> None:
    assert create_app().title == Settings.from_env().api_title
