from fastapi.testclient import TestClient

# API key para tests (debe coincidir con conftest.py)
TEST_API_KEY = "test-api-key-12345"

CELL_PAYLOAD = {
    "name": "Celda_01",
    "location": "Techo Norte",
    "rated_voltage": 5.0,
    "efficiency_threshold": 80.0,
}


def test_create_returns_201_with_derived_safe_voltage(client: TestClient) -> None:
    response = client.post("/api/v1/cells", json=CELL_PAYLOAD, headers={"X-API-Key": TEST_API_KEY})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Celda_01"
    assert body["max_safe_voltage"] == 6.0
    assert body["is_active"] is True


def test_create_rejects_a_duplicate_name_with_409(client: TestClient) -> None:
    client.post("/api/v1/cells", json=CELL_PAYLOAD, headers={"X-API-Key": TEST_API_KEY})

    response = client.post("/api/v1/cells", json=CELL_PAYLOAD, headers={"X-API-Key": TEST_API_KEY})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_rejects_invalid_payloads_with_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/cells",
        json={"name": "X", "location": "Techo", "rated_voltage": -1},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 422


def test_list_returns_every_cell(client: TestClient, created_cell: dict[str, object]) -> None:
    response = client.get("/api/v1/cells")

    assert response.status_code == 200
    assert [cell["id"] for cell in response.json()] == [created_cell["id"]]


def test_list_active_hides_deactivated_cells(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    client.put(
        f"/api/v1/cells/{created_cell['id']}",
        json={"is_active": False},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert client.get("/api/v1/cells/active").json() == []
    assert len(client.get("/api/v1/cells").json()) == 1


def test_get_returns_the_requested_cell(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.get(f"/api/v1/cells/{created_cell['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created_cell["id"]


def test_get_returns_404_for_an_unknown_cell(client: TestClient) -> None:
    response = client.get("/api/v1/cells/404")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_recomputes_safe_voltage(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.put(
        f"/api/v1/cells/{created_cell['id']}",
        json={"rated_voltage": 10.0},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 200
    assert response.json()["max_safe_voltage"] == 12.0


def test_update_returns_404_for_an_unknown_cell(client: TestClient) -> None:
    assert (
        client.put(
            "/api/v1/cells/404", json={"location": "X"}, headers={"X-API-Key": TEST_API_KEY}
        ).status_code
        == 404
    )


def test_update_returns_409_when_the_name_is_taken(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    other = client.post(
        "/api/v1/cells",
        json={"name": "Celda_02", "location": "Techo Sur", "rated_voltage": 5.0},
        headers={"X-API-Key": TEST_API_KEY},
    ).json()

    response = client.put(
        f"/api/v1/cells/{other['id']}",
        json={"name": "Celda_01"},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 409


def test_delete_returns_204_and_removes_the_cell(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    assert (
        client.delete(
            f"/api/v1/cells/{created_cell['id']}", headers={"X-API-Key": TEST_API_KEY}
        ).status_code
        == 204
    )
    assert client.get(f"/api/v1/cells/{created_cell['id']}").status_code == 404


def test_delete_returns_404_for_an_unknown_cell(client: TestClient) -> None:
    assert (
        client.delete("/api/v1/cells/404", headers={"X-API-Key": TEST_API_KEY}).status_code == 404
    )


def test_delete_cascades_to_readings(client: TestClient, created_cell: dict[str, object]) -> None:
    client.post(
        "/api/v1/readings",
        json={"cell_id": created_cell["id"], "voltage_measured": 4.5},
        headers={"X-API-Key": TEST_API_KEY},
    )

    client.delete(f"/api/v1/cells/{created_cell['id']}", headers={"X-API-Key": TEST_API_KEY})

    assert client.get("/api/v1/readings").json() == []


# Tests de autenticación con API key
def test_post_cell_without_api_key_returns_401(client: TestClient) -> None:
    response = client.post("/api/v1/cells", json=CELL_PAYLOAD)

    assert response.status_code == 401


def test_post_cell_with_wrong_api_key_returns_401(client: TestClient) -> None:
    response = client.post("/api/v1/cells", json=CELL_PAYLOAD, headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401


def test_put_cell_without_api_key_returns_401(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.put(f"/api/v1/cells/{created_cell['id']}", json={"location": "New Location"})

    assert response.status_code == 401


def test_put_cell_with_wrong_api_key_returns_401(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.put(
        f"/api/v1/cells/{created_cell['id']}",
        json={"location": "New Location"},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_delete_cell_without_api_key_returns_401(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.delete(f"/api/v1/cells/{created_cell['id']}")

    assert response.status_code == 401


def test_delete_cell_with_wrong_api_key_returns_401(
    client: TestClient, created_cell: dict[str, object]
) -> None:
    response = client.delete(
        f"/api/v1/cells/{created_cell['id']}", headers={"X-API-Key": "wrong-key"}
    )

    assert response.status_code == 401
