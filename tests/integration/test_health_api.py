import pytest
from fastapi.testclient import TestClient

from main import create_app
from utils.config import Settings


def test_root_identifies_the_api(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Solaris Monitoring" in response.text


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service_status"] == "operational"


def test_health_reports_invalid_update_date(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UPDATE_DATE", "not-a-date")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["service_status"] == "degraded"


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
