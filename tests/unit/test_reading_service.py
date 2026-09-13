from datetime import datetime, timedelta

import pytest

from tests.fakes import InMemoryCellRepository, InMemoryReadingRepository, make_cell, make_reading
from utils.clock import utc_now
from utils.domain.analysis import (
    CompositeAnomalyDetector,
    LowEfficiencyAnomalyDetector,
    OverVoltageAnomalyDetector,
    RatioEfficiencyCalculator,
    ReadingAnalyzer,
)
from utils.domain.errors import (
    CellNotFoundError,
    InactiveCellError,
    NoReadingsInPeriodError,
    ReadingNotFoundError,
)
from utils.repositories.protocols import CellLookup, ReadingRepository
from utils.schemas.reading import ReadingCreate
from utils.services.reading_service import ReadingService


def build_analyzer() -> ReadingAnalyzer:
    return ReadingAnalyzer(
        calculator=RatioEfficiencyCalculator(),
        detector=CompositeAnomalyDetector(
            [OverVoltageAnomalyDetector(), LowEfficiencyAnomalyDetector()]
        ),
    )


def build_service(
    cells: InMemoryCellRepository | None = None,
    readings: InMemoryReadingRepository | None = None,
) -> ReadingService:
    cell_lookup: CellLookup = cells if cells is not None else InMemoryCellRepository()
    reading_repo: ReadingRepository = (
        readings if readings is not None else InMemoryReadingRepository()
    )
    return ReadingService(readings=reading_repo, cells=cell_lookup, analyzer=build_analyzer())


def test_create_computes_efficiency_from_the_cell_rating() -> None:
    service = build_service(InMemoryCellRepository([make_cell()]))

    reading = service.create(ReadingCreate(cell_id=1, voltage_measured=4.85))

    assert reading.efficiency_percentage == 97.0
    assert reading.is_anomaly is False


def test_create_flags_over_voltage_as_anomaly() -> None:
    service = build_service(InMemoryCellRepository([make_cell()]))

    assert service.create(ReadingCreate(cell_id=1, voltage_measured=7.0)).is_anomaly is True


def test_create_flags_under_performance_as_anomaly() -> None:
    service = build_service(InMemoryCellRepository([make_cell()]))

    reading = service.create(ReadingCreate(cell_id=1, voltage_measured=2.0))

    assert reading.efficiency_percentage == 40.0
    assert reading.is_anomaly is True


def test_create_keeps_the_timestamp_reported_by_the_device() -> None:
    service = build_service(InMemoryCellRepository([make_cell()]))
    reported = utc_now() - timedelta(hours=3)

    reading = service.create(ReadingCreate(cell_id=1, voltage_measured=4.5, timestamp=reported))

    assert reading.timestamp == reported


def test_create_defaults_the_timestamp_to_now() -> None:
    service = build_service(InMemoryCellRepository([make_cell()]))
    before = utc_now()

    reading = service.create(ReadingCreate(cell_id=1, voltage_measured=4.5))

    assert before <= reading.timestamp <= utc_now()


def test_create_rejects_an_unknown_cell() -> None:
    with pytest.raises(CellNotFoundError):
        build_service().create(ReadingCreate(cell_id=404, voltage_measured=4.5))


def test_create_rejects_an_inactive_cell() -> None:
    service = build_service(InMemoryCellRepository([make_cell(is_active=False)]))

    with pytest.raises(InactiveCellError):
        service.create(ReadingCreate(cell_id=1, voltage_measured=4.5))


def test_get_raises_when_reading_is_missing() -> None:
    with pytest.raises(ReadingNotFoundError):
        build_service().get(404)


def test_list_all_respects_the_limit() -> None:
    now = utc_now()
    readings = InMemoryReadingRepository(
        [make_reading(i, 1, 4.5, 90.0, now - timedelta(minutes=i)) for i in range(1, 6)]
    )
    service = build_service(InMemoryCellRepository([make_cell()]), readings)

    assert len(service.list_all(limit=3)) == 3


def test_list_by_cell_rejects_an_unknown_cell() -> None:
    with pytest.raises(CellNotFoundError):
        build_service().list_by_cell(404, limit=10)


def test_list_by_cell_returns_newest_first() -> None:
    now = utc_now()
    readings = InMemoryReadingRepository(
        [
            make_reading(1, 1, 4.0, 80.0, now - timedelta(hours=2)),
            make_reading(2, 1, 4.5, 90.0, now - timedelta(hours=1)),
            make_reading(3, 2, 4.9, 98.0, now),
        ]
    )
    service = build_service(InMemoryCellRepository([make_cell(), make_cell(2, "otra")]), readings)

    result = service.list_by_cell(1, limit=10)

    assert [r.id for r in result] == [2, 1]


def test_summary_aggregates_readings_in_the_period() -> None:
    now = utc_now()
    readings = InMemoryReadingRepository(
        [
            make_reading(1, 1, 4.0, 80.0, now - timedelta(days=1)),
            make_reading(2, 1, 5.0, 100.0, now, is_anomaly=True),
        ]
    )
    service = build_service(InMemoryCellRepository([make_cell()]), readings)

    summary = service.summary_for_cell(1, days=7)

    assert summary.reading_count == 2
    assert summary.avg_voltage == 4.5
    assert summary.max_voltage == 5.0
    assert summary.min_voltage == 4.0
    assert summary.avg_efficiency == 90.0
    assert summary.anomaly_count == 1
    assert summary.cell_name == "Celda_01"
    assert summary.period_days == 7


def test_summary_ignores_readings_outside_the_window() -> None:
    old: datetime = utc_now() - timedelta(days=30)
    readings = InMemoryReadingRepository([make_reading(1, 1, 4.0, 80.0, old)])
    service = build_service(InMemoryCellRepository([make_cell()]), readings)

    with pytest.raises(NoReadingsInPeriodError):
        service.summary_for_cell(1, days=7)


def test_summary_rejects_an_unknown_cell() -> None:
    with pytest.raises(CellNotFoundError):
        build_service().summary_for_cell(404, days=7)
