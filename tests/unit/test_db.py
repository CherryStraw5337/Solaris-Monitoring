from typing import Any

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

import db as db_module
from db import create_db_engine, get_db


def test_sqlite_engine_allows_cross_thread_access(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_create_engine(url: str, **kwargs: Any) -> object:
        captured.update({"url": url, "kwargs": kwargs})
        return object()

    monkeypatch.setattr(db_module, "create_engine", fake_create_engine)
    create_db_engine("sqlite:///local.db")

    assert captured["kwargs"]["connect_args"] == {"check_same_thread": False}


def test_non_sqlite_engine_enables_pool_pre_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_create_engine(url: str, **kwargs: Any) -> object:
        captured.update({"url": url, "kwargs": kwargs})
        return object()

    monkeypatch.setattr(db_module, "create_engine", fake_create_engine)
    create_db_engine("postgresql+psycopg://user:pass@host:5432/db")

    assert captured["kwargs"] == {"pool_pre_ping": True}


def test_sqlite_engine_is_usable() -> None:
    engine = create_db_engine("sqlite://")
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("select 1")) == 1
    finally:
        engine.dispose()


def test_get_db_closes_the_session(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[str] = []

    class TrackingSession(Session):
        def close(self) -> None:
            closed.append("closed")
            super().close()

    monkeypatch.setattr(
        db_module, "SessionLocal", sessionmaker(bind=engine, class_=TrackingSession)
    )

    generator = get_db()
    session = next(generator)
    assert isinstance(session, Session)
    assert closed == []

    with pytest.raises(StopIteration):
        next(generator)
    assert closed == ["closed"]
