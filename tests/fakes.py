from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from utils.clock import utc_now
from utils.models import PhotovoltaicCell, Reading


def make_cell(
    cell_id: int = 1,
    name: str = "Celda_01",
    rated_voltage: float = 5.0,
    max_safe_voltage: float = 6.0,
    efficiency_threshold: float = 80.0,
    is_active: bool = True,
) -> PhotovoltaicCell:
    cell = PhotovoltaicCell(
        name=name,
        location="Techo Norte",
        rated_voltage=rated_voltage,
        max_safe_voltage=max_safe_voltage,
        efficiency_threshold=efficiency_threshold,
        is_active=is_active,
    )
    cell.id = cell_id
    return cell


def make_reading(
    reading_id: int,
    cell_id: int,
    voltage: float,
    efficiency: float,
    timestamp: datetime,
    is_anomaly: bool = False,
) -> Reading:
    reading = Reading(
        cell_id=cell_id,
        voltage_measured=voltage,
        efficiency_percentage=efficiency,
        is_anomaly=is_anomaly,
        timestamp=timestamp,
    )
    reading.id = reading_id
    reading.created_at = timestamp
    return reading


class InMemoryCellRepository:
    def __init__(self, cells: list[PhotovoltaicCell] | None = None) -> None:
        self._cells: dict[int, PhotovoltaicCell] = {c.id: c for c in cells or []}
        self._next_id = max(self._cells, default=0) + 1

    def add(self, cell: PhotovoltaicCell) -> PhotovoltaicCell:
        cell.id = self._next_id
        self._next_id += 1
        self._cells[cell.id] = cell
        return cell

    def get_by_id(self, cell_id: int) -> PhotovoltaicCell | None:
        return self._cells.get(cell_id)

    def get_by_name(self, name: str) -> PhotovoltaicCell | None:
        return next((c for c in self._cells.values() if c.name == name), None)

    def list_all(self) -> list[PhotovoltaicCell]:
        return list(self._cells.values())

    def list_active(self) -> list[PhotovoltaicCell]:
        return [c for c in self._cells.values() if c.is_active]

    def apply_changes(self, cell: PhotovoltaicCell, changes: Mapping[str, Any]) -> PhotovoltaicCell:
        for field, value in changes.items():
            setattr(cell, field, value)
        return cell

    def delete(self, cell: PhotovoltaicCell) -> None:
        self._cells.pop(cell.id, None)


class InMemoryReadingRepository:
    def __init__(self, readings: list[Reading] | None = None) -> None:
        self._readings: dict[int, Reading] = {r.id: r for r in readings or []}
        self._next_id = max(self._readings, default=0) + 1

    def add(self, reading: Reading) -> Reading:
        reading.id = self._next_id
        self._next_id += 1
        if reading.created_at is None:
            reading.created_at = utc_now()
        self._readings[reading.id] = reading
        return reading

    def get_by_id(self, reading_id: int) -> Reading | None:
        return self._readings.get(reading_id)

    def list_all(self, limit: int) -> list[Reading]:
        return self._sorted(self._readings.values())[:limit]

    def list_by_cell(self, cell_id: int, limit: int) -> list[Reading]:
        matches = [r for r in self._readings.values() if r.cell_id == cell_id]
        return self._sorted(matches)[:limit]

    def list_since(self, cell_id: int, since: datetime) -> list[Reading]:
        matches = [
            r for r in self._readings.values() if r.cell_id == cell_id and r.timestamp >= since
        ]
        return self._sorted(matches)

    @staticmethod
    def _sorted(readings: Iterable[Reading]) -> list[Reading]:
        return sorted(readings, key=lambda r: (r.timestamp, r.id), reverse=True)
