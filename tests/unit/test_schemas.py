from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from utils.clock import utc_now
from utils.schemas.cell import CellCreate
from utils.schemas.reading import ReadingCreate


def test_reading_defaults_timestamp_to_none() -> None:
    assert ReadingCreate(cell_id=1, voltage_measured=4.5).timestamp is None


def test_reading_accepts_an_explicit_null_timestamp() -> None:
    assert ReadingCreate(cell_id=1, voltage_measured=4.5, timestamp=None).timestamp is None


def test_reading_rejects_non_positive_voltage() -> None:
    with pytest.raises(ValidationError):
        ReadingCreate(cell_id=1, voltage_measured=0.0)


def test_reading_rejects_non_positive_cell_id() -> None:
    with pytest.raises(ValidationError):
        ReadingCreate(cell_id=0, voltage_measured=4.5)


def test_reading_rejects_a_timestamp_far_in_the_future() -> None:
    with pytest.raises(ValidationError, match="future"):
        ReadingCreate(
            cell_id=1,
            voltage_measured=4.5,
            timestamp=utc_now() + timedelta(hours=2),
        )


def test_reading_tolerates_small_device_clock_drift() -> None:
    drifted = utc_now() + timedelta(minutes=2)

    assert ReadingCreate(cell_id=1, voltage_measured=4.5, timestamp=drifted).timestamp == drifted


def test_reading_assumes_utc_for_naive_timestamps() -> None:
    payload = ReadingCreate(
        cell_id=1, voltage_measured=4.5, timestamp=datetime(2026, 9, 11, 14, 30)
    )

    assert payload.timestamp == datetime(2026, 9, 11, 14, 30, tzinfo=UTC)


def test_reading_normalizes_other_offsets_to_utc() -> None:
    bogota = timezone(timedelta(hours=-5))
    payload = ReadingCreate(
        cell_id=1, voltage_measured=4.5, timestamp=datetime(2026, 9, 11, 9, 30, tzinfo=bogota)
    )

    assert payload.timestamp == datetime(2026, 9, 11, 14, 30, tzinfo=UTC)


def test_cell_rejects_non_positive_rated_voltage() -> None:
    with pytest.raises(ValidationError):
        CellCreate(name="Celda", location="Techo", rated_voltage=0.0)


def test_cell_rejects_a_blank_name() -> None:
    with pytest.raises(ValidationError):
        CellCreate(name="", location="Techo", rated_voltage=5.0)


@pytest.mark.parametrize("threshold", [-1.0, 101.0])
def test_cell_keeps_threshold_within_percentage_bounds(threshold: float) -> None:
    with pytest.raises(ValidationError):
        CellCreate(
            name="Celda", location="Techo", rated_voltage=5.0, efficiency_threshold=threshold
        )


def test_cell_threshold_defaults_to_eighty_percent() -> None:
    cell = CellCreate(name="Celda", location="Techo", rated_voltage=5.0)

    assert cell.efficiency_threshold == 80.0
