from datetime import timedelta

from fastapi.testclient import TestClient

from utils.clock import utc_now

# API key para tests (debe coincidir con conftest.py)
TEST_API_KEY = "test-api-key-12345"


def post_reading(
    client: TestClient, cell_id: object, voltage: float, api_key: str | None = None
) -> dict[str, object]:
    headers = {}
    if api_key is not None:
        headers["X-API-Key"] = api_key
    elif api_key is None:
        # Por defecto, incluir la clave correcta en tests existentes
        headers["X-API-Key"] = TEST_API_KEY

    response = client.post(
        "/api/v1/readings", json={"cell_id": cell_id, "voltage_measured": voltage}, headers=headers
    )
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def test_create_returns_201_with_computed_efficiency(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    body = post_reading(client, created_cell["id"], 4.85)

    assert body["efficiency_percentage"] == 97.0
    assert body["is_anomaly"] is False


def test_create_flags_over_voltage(client: TestClient, created_cell: dict[str, object]) -> None:
    assert post_reading(client, created_cell["id"], 7.0)["is_anomaly"] is True


def test_create_flags_low_efficiency(client: TestClient, created_cell: dict[str, object]) -> None:
    body = post_reading(client, created_cell["id"], 2.0)

    assert body["efficiency_percentage"] == 40.0
    assert body["is_anomaly"] is True


def test_create_accepts_a_device_timestamp(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/readings",
        json={
            "cell_id": created_cell["id"],
            "voltage_measured": 4.5,
            "timestamp": "2026-09-11T14:30:00Z",
        },
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 201
    assert response.json()["timestamp"].startswith("2026-09-11T14:30:00")


def test_create_rejects_a_future_timestamp_with_422(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/readings",
        json={
            "cell_id": created_cell["id"],
            "voltage_measured": 4.5,
            "timestamp": (utc_now() + timedelta(days=1)).isoformat(),
        },
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 422


def test_create_returns_404_for_an_unknown_cell(client: TestClient) -> None:
    response = client.post(
        "/api/v1/readings",
        json={"cell_id": 404, "voltage_measured": 4.5},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 404


def test_create_returns_409_for_an_inactive_cell(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    client.put(
        f"/api/v1/cells/{created_cell['id']}",
        json={"is_active": False},
        headers={"X-API-Key": TEST_API_KEY},
    )

    response = client.post(
        "/api/v1/readings",
        json={"cell_id": created_cell["id"], "voltage_measured": 4.5},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 409
    assert "inactive" in response.json()["detail"]


def test_create_rejects_non_positive_voltage_with_422(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/readings",
        json={"cell_id": created_cell["id"], "voltage_measured": 0},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 422


def test_list_returns_every_reading(client: TestClient, created_cell: dict[str, object]) -> None:
    post_reading(client, created_cell["id"], 4.5)
    post_reading(client, created_cell["id"], 4.6)

    assert len(client.get("/api/v1/readings").json()) == 2


def test_list_honours_the_limit_query(client: TestClient, created_cell: dict[str, object]) -> None:
    for voltage in (4.1, 4.2, 4.3):
        post_reading(client, created_cell["id"], voltage)

    assert len(client.get("/api/v1/readings?limit=2").json()) == 2


def test_list_rejects_an_out_of_range_limit(client: TestClient) -> None:
    assert client.get("/api/v1/readings?limit=0").status_code == 422


def test_get_returns_the_requested_reading(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    created = post_reading(client, created_cell["id"], 4.5)

    response = client.get(f"/api/v1/readings/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_returns_404_for_an_unknown_reading(client: TestClient) -> None:
    assert client.get("/api/v1/readings/404").status_code == 404


def test_list_by_cell_returns_only_that_cell(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    other = client.post(
        "/api/v1/cells",
        json={"name": "Celda_02", "location": "Techo Sur", "rated_voltage": 5.0},
        headers={"X-API-Key": TEST_API_KEY},
    ).json()
    post_reading(client, created_cell["id"], 4.5)
    post_reading(client, other["id"], 4.6)

    body = client.get(f"/api/v1/readings/cell/{created_cell['id']}").json()

    assert [row["cell_id"] for row in body] == [created_cell["id"]]


def test_list_by_cell_returns_404_for_an_unknown_cell(client: TestClient) -> None:
    assert client.get("/api/v1/readings/cell/404").status_code == 404


def test_summary_aggregates_the_period(client: TestClient, created_cell: dict[str, object]) -> None:
    post_reading(client, created_cell["id"], 4.0)
    post_reading(client, created_cell["id"], 5.0)

    body = client.get(f"/api/v1/readings/cell/{created_cell['id']}/summary").json()

    assert body["reading_count"] == 2
    assert body["avg_voltage"] == 4.5
    assert body["max_voltage"] == 5.0
    assert body["min_voltage"] == 4.0
    assert body["avg_efficiency"] == 90.0
    assert body["anomaly_count"] == 0
    assert body["period_days"] == 7


def test_summary_returns_404_when_the_period_is_empty(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.get(f"/api/v1/readings/cell/{created_cell['id']}/summary")

    assert response.status_code == 404


def test_summary_rejects_an_out_of_range_period(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    url = f"/api/v1/readings/cell/{created_cell['id']}/summary?days=400"

    assert client.get(url).status_code == 422


# Tests de autenticación con API key
def test_post_reading_without_api_key_returns_401(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/readings", json={"cell_id": created_cell["id"], "voltage_measured": 4.5}
    )

    assert response.status_code == 401


def test_post_reading_with_wrong_api_key_returns_401(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/readings",
        json={"cell_id": created_cell["id"], "voltage_measured": 4.5},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_post_reading_with_correct_api_key_succeeds(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/readings",
        json={"cell_id": created_cell["id"], "voltage_measured": 4.5},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 201
