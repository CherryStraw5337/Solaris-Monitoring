from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import PUBLIC_DIR, create_app
from utils.config import Settings

REPO_PUBLIC_DIR = Path(__file__).resolve().parents[2] / "src" / "public"


def test_root_identifies_the_api(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Solaris Monitoring" in response.text


def test_landing_is_served_from_src_public() -> None:
    assert PUBLIC_DIR.resolve() == REPO_PUBLIC_DIR


def test_root_serves_the_current_landing_page(client: TestClient) -> None:
    response = client.get("/")

    assert response.headers["content-type"].startswith("text/html")
    assert response.content == (REPO_PUBLIC_DIR / "index.html").read_bytes()


@pytest.mark.parametrize(
    ("path", "content_type"),
    [
        ("/style.css", "text/css"),
        ("/main.js", "text/javascript"),
        ("/resource/paneles.jpg", "image/jpeg"),
    ],
)
def test_landing_assets_are_reachable(client: TestClient, path: str, content_type: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)


def test_static_mount_does_not_shadow_the_api(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/api/v1/cells").status_code == 200
    assert client.get("/no-existe.css").status_code == 404


def test_health_reports_the_deployed_commit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "beb25f2abc")
    monkeypatch.setenv("RENDER_GIT_BRANCH", "main")

    body = client.get("/health").json()

    assert body["commit"] == "beb25f2abc"
    assert body["branch"] == "main"


def test_health_marks_commit_as_local_outside_render(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("RENDER_GIT_BRANCH", raising=False)

    body = client.get("/health").json()

    assert body["commit"] == "local"
    assert body["branch"] == "local"


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
