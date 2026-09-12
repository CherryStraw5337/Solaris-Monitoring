import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from edsia_beyond.domain.errors import CellNotFoundError, DomainError
from edsia_beyond.exception_handlers import register_exception_handlers


class UnmappedDomainError(DomainError):
    """Error de dominio sin entrada en la tabla de estados HTTP."""


@pytest.fixture
def error_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/unmapped")
    def raise_unmapped() -> None:
        raise UnmappedDomainError("algo salió mal")

    @app.get("/mapped")
    def raise_mapped() -> None:
        raise CellNotFoundError(7)

    return TestClient(app, raise_server_exceptions=False)


def test_unmapped_domain_errors_default_to_400(error_client: TestClient) -> None:
    response = error_client.get("/unmapped")

    assert response.status_code == 400
    assert response.json()["detail"] == "algo salió mal"


def test_mapped_domain_errors_use_their_status(error_client: TestClient) -> None:
    response = error_client.get("/mapped")

    assert response.status_code == 404
    assert "7" in response.json()["detail"]
