from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from utils.clock import utc_now
from utils.models import PhotovoltaicCell, Reading
from utils.repositories.cell_repo import SqlAlchemyCellRepository
from utils.repositories.protocols import CellRepository, ReadingRepository
from utils.repositories.reading_repo import SqlAlchemyReadingRepository


def new_cell(name: str = "Celda_01", is_active: bool = True) -> PhotovoltaicCell:
    return PhotovoltaicCell(
        name=name,
        location="Techo",
        rated_voltage=5.0,
        max_safe_voltage=6.0,
        efficiency_threshold=80.0,
        is_active=is_active,
    )


def test_sqlalchemy_repositories_satisfy_their_protocols(db_session: Session) -> None:
    cells: CellRepository = SqlAlchemyCellRepository(db_session)
    readings: ReadingRepository = SqlAlchemyReadingRepository(db_session)

    assert cells.list_all() == []
    assert readings.list_all(limit=10) == []


def test_cell_is_persisted_and_retrievable_by_id_and_name(db_session: Session) -> None:
    repo = SqlAlchemyCellRepository(db_session)

    stored = repo.add(new_cell())

    assert stored.id is not None
    assert repo.get_by_id(stored.id) is stored
    assert repo.get_by_name("Celda_01") is stored


def test_get_by_name_returns_none_for_unknown_names(db_session: Session) -> None:
    assert SqlAlchemyCellRepository(db_session).get_by_name("no-existe") is None


def test_list_active_filters_out_inactive_cells(db_session: Session) -> None:
    repo = SqlAlchemyCellRepository(db_session)
    repo.add(new_cell("activa"))
    repo.add(new_cell("inactiva", is_active=False))

    assert [cell.name for cell in repo.list_active()] == ["activa"]
    assert len(repo.list_all()) == 2


def test_apply_changes_persists_the_update(db_session: Session) -> None:
    repo = SqlAlchemyCellRepository(db_session)
    cell = repo.add(new_cell())

    repo.apply_changes(cell, {"location": "Techo Sur", "is_active": False})
    db_session.expire_all()

    reloaded = repo.get_by_id(cell.id)
    assert reloaded is not None
    assert reloaded.location == "Techo Sur"
    assert reloaded.is_active is False


def test_deleting_a_cell_also_removes_its_readings(db_session: Session) -> None:
    cells = SqlAlchemyCellRepository(db_session)
    readings = SqlAlchemyReadingRepository(db_session)
    cell = cells.add(new_cell())
    readings.add(
        Reading(
            cell_id=cell.id,
            voltage_measured=4.5,
            efficiency_percentage=90.0,
            is_anomaly=False,
            timestamp=utc_now(),
        )
    )

    cells.delete(cell)

    assert db_session.scalars(select(Reading)).all() == []


def test_readings_are_listed_newest_first(db_session: Session) -> None:
    cells = SqlAlchemyCellRepository(db_session)
    repo = SqlAlchemyReadingRepository(db_session)
    cell = cells.add(new_cell())
    now = utc_now()
    for offset in (2, 0, 1):
        repo.add(
            Reading(
                cell_id=cell.id,
                voltage_measured=4.5,
                efficiency_percentage=90.0,
                is_anomaly=False,
                timestamp=now - timedelta(hours=offset),
            )
        )

    stored = repo.list_by_cell(cell.id, limit=10)

    assert [row.timestamp for row in stored] == sorted(
        (row.timestamp for row in stored), reverse=True
    )


def test_list_since_excludes_older_readings(db_session: Session) -> None:
    cells = SqlAlchemyCellRepository(db_session)
    repo = SqlAlchemyReadingRepository(db_session)
    cell = cells.add(new_cell())
    now = utc_now()
    for offset_days in (0, 30):
        repo.add(
            Reading(
                cell_id=cell.id,
                voltage_measured=4.5,
                efficiency_percentage=90.0,
                is_anomaly=False,
                timestamp=now - timedelta(days=offset_days),
            )
        )

    recent = repo.list_since(cell.id, now - timedelta(days=7))

    assert len(recent) == 1


def test_get_by_id_returns_none_for_unknown_reading(db_session: Session) -> None:
    assert SqlAlchemyReadingRepository(db_session).get_by_id(404) is None


def test_timestamps_survive_the_roundtrip_as_utc(db_session: Session) -> None:
    cells = SqlAlchemyCellRepository(db_session)
    repo = SqlAlchemyReadingRepository(db_session)
    cell = cells.add(new_cell())
    bogota = timezone(timedelta(hours=-5))
    reading = repo.add(
        Reading(
            cell_id=cell.id,
            voltage_measured=4.5,
            efficiency_percentage=90.0,
            is_anomaly=False,
            timestamp=datetime(2026, 9, 11, 9, 30, tzinfo=bogota),
        )
    )
    db_session.expire_all()

    stored = repo.get_by_id(reading.id)

    assert stored is not None
    assert stored.timestamp == datetime(2026, 9, 11, 14, 30, tzinfo=UTC)
    assert stored.timestamp.tzinfo is not None
    assert stored.created_at.tzinfo is not None
