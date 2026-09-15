import re
from pathlib import Path

from fastapi.testclient import TestClient

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "src" / "public"
DASHBOARD_JS = (PUBLIC_DIR / "main.js").read_text(encoding="utf-8")
DASHBOARD_HTML = (PUBLIC_DIR / "index.html").read_text(encoding="utf-8")

# Captura "/health" y rutas "/api/v1/..." escritas en el JS, con o sin ${...}.
API_PATH_PATTERN = re.compile(r"['\"`](/health|/api/v1/[A-Za-z0-9_/${}.-]*)")


def _as_openapi_template(path: str) -> str:
    return re.sub(r"\$\{[^}]+\}", "{param}", path.split("?")[0].rstrip("/"))


def _openapi_get_paths(client: TestClient) -> set[str]:
    schema = client.get("/openapi.json").json()
    return {
        re.sub(r"\{[^}]+\}", "{param}", path)
        for path, operations in schema["paths"].items()
        if "get" in operations
    }


def test_dashboard_uses_api_paths() -> None:
    assert API_PATH_PATTERN.findall(DASHBOARD_JS), "el dashboard debe consumir la API"


def test_dashboard_only_calls_existing_get_endpoints(client: TestClient) -> None:
    available = _openapi_get_paths(client)

    used = {_as_openapi_template(path) for path in API_PATH_PATTERN.findall(DASHBOARD_JS)}

    assert used, "no se encontraron rutas de la API en main.js"
    assert used <= available, f"rutas inexistentes o no GET: {sorted(used - available)}"


def test_dashboard_never_sends_write_requests() -> None:
    assert not re.search(r"method\s*:\s*['\"](POST|PUT|PATCH|DELETE)", DASHBOARD_JS, re.I)


def test_dashboard_does_not_handle_the_device_api_key() -> None:
    for source in (DASHBOARD_JS, DASHBOARD_HTML):
        assert "X-API-Key" not in source
        assert "Authorization" not in source


def test_dashboard_escapes_api_text_before_rendering() -> None:
    # Nombres y ubicaciones de celdas vienen de la API: sin escape habría XSS vía innerHTML.
    assert "function escapeHtml" in DASHBOARD_JS


def test_external_scripts_are_pinned_to_a_version() -> None:
    scripts = re.findall(r"<script[^>]+src=\"(https://[^\"]+)\"", DASHBOARD_HTML)

    assert scripts, "se esperaban dependencias externas (Tailwind y Chart.js)"
    for url in scripts:
        assert re.search(r"\d+\.\d+\.\d+", url), f"dependencia sin versión fija: {url}"
