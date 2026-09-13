from __future__ import annotations

from datetime import timedelta

from utils.clock import utc_now
from utils.domain.analysis import CellSpec, ReadingAnalyzer
from utils.domain.errors import (
    CellNotFoundError,
    InactiveCellError,
    NoReadingsInPeriodError,
    ReadingNotFoundError,
)
from utils.models import PhotovoltaicCell, Reading
from utils.repositories.protocols import CellLookup, ReadingRepository
from utils.schemas.reading import ReadingCreate, ReadingOut, ReadingSummary


class ReadingService:
    def __init__(
        self,
        readings: ReadingRepository,
        cells: CellLookup,
        analyzer: ReadingAnalyzer,
    ) -> None:
        self._readings = readings
        self._cells = cells
        self._analyzer = analyzer

    def create(self, payload: ReadingCreate) -> ReadingOut:
        cell = self._require_cell(payload.cell_id)
        if not cell.is_active:
            raise InactiveCellError(cell.id)

        analysis = self._analyzer.analyze(payload.voltage_measured, _spec_of(cell))
        reading = Reading(
            cell_id=cell.id,
            voltage_measured=payload.voltage_measured,
            efficiency_percentage=analysis.efficiency_percentage,
            is_anomaly=analysis.is_anomaly,
            timestamp=payload.timestamp or utc_now(),
        )
        return ReadingOut.model_validate(self._readings.add(reading))

    def get(self, reading_id: int) -> ReadingOut:
        reading = self._readings.get_by_id(reading_id)
        if reading is None:
            raise ReadingNotFoundError(reading_id)
        return ReadingOut.model_validate(reading)

    def list_all(self, limit: int) -> list[ReadingOut]:
        return [ReadingOut.model_validate(row) for row in self._readings.list_all(limit)]

    def list_by_cell(self, cell_id: int, limit: int) -> list[ReadingOut]:
        self._require_cell(cell_id)
        return [
            ReadingOut.model_validate(row) for row in self._readings.list_by_cell(cell_id, limit)
        ]

    def summary_for_cell(self, cell_id: int, days: int) -> ReadingSummary:
        cell = self._require_cell(cell_id)
        rows = self._readings.list_since(cell_id, utc_now() - timedelta(days=days))
        if not rows:
            raise NoReadingsInPeriodError(cell_id, days)

        voltages = [row.voltage_measured for row in rows]
        efficiencies = [row.efficiency_percentage for row in rows]
        return ReadingSummary(
            cell_id=cell_id,
            cell_name=cell.name,
            period_days=days,
            reading_count=len(rows),
            avg_voltage=round(sum(voltages) / len(voltages), 2),
            max_voltage=max(voltages),
            min_voltage=min(voltages),
            avg_efficiency=round(sum(efficiencies) / len(efficiencies), 2),
            anomaly_count=sum(1 for row in rows if row.is_anomaly),
        )

    def _require_cell(self, cell_id: int) -> PhotovoltaicCell:
        cell = self._cells.get_by_id(cell_id)
        if cell is None:
            raise CellNotFoundError(cell_id)
        return cell


def _spec_of(cell: PhotovoltaicCell) -> CellSpec:
    return CellSpec(
        rated_voltage=cell.rated_voltage,
        max_safe_voltage=cell.max_safe_voltage,
        efficiency_threshold=cell.efficiency_threshold,
    )
