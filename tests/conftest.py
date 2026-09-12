from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from edsia_beyond.db import Base, get_db
from edsia_beyond.main import create_app


@pytest.fixture
def engine() -> Iterator[Engine]:
    # StaticPool mantiene una única conexión: sin él, el hilo del TestClient abre
    # otra conexión y encuentra una base ":memory:" vacía.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app(engine: Engine) -> FastAPI:
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db() -> Iterator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def created_cell(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/cells",
        json={
            "name": "Celda_01",
            "location": "Techo Norte",
            "rated_voltage": 5.0,
            "efficiency_threshold": 80.0,
        },
    )
    assert response.status_code == 201
    payload: dict[str, object] = response.json()
    return payload
