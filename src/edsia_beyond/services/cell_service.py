from __future__ import annotations

from typing import Any

from edsia_beyond.domain.analysis import safe_voltage_limit
from edsia_beyond.domain.errors import CellNotFoundError, DuplicateCellNameError
from edsia_beyond.models import PhotovoltaicCell
from edsia_beyond.repositories.protocols import CellRepository
from edsia_beyond.schemas.cell import CellCreate, CellOut, CellUpdate


class CellService:
    def __init__(self, cells: CellRepository) -> None:
        self._cells = cells

    def create(self, payload: CellCreate) -> CellOut:
        if self._cells.get_by_name(payload.name) is not None:
            raise DuplicateCellNameError(payload.name)

        cell = PhotovoltaicCell(
            name=payload.name,
            location=payload.location,
            rated_voltage=payload.rated_voltage,
            max_safe_voltage=safe_voltage_limit(payload.rated_voltage),
            efficiency_threshold=payload.efficiency_threshold,
            is_active=True,
        )
        return CellOut.model_validate(self._cells.add(cell))

    def get(self, cell_id: int) -> CellOut:
        return CellOut.model_validate(self._require_cell(cell_id))

    def list_all(self) -> list[CellOut]:
        return [CellOut.model_validate(cell) for cell in self._cells.list_all()]

    def list_active(self) -> list[CellOut]:
        return [CellOut.model_validate(cell) for cell in self._cells.list_active()]

    def update(self, cell_id: int, payload: CellUpdate) -> CellOut:
        cell = self._require_cell(cell_id)
        changes: dict[str, Any] = payload.model_dump(exclude_unset=True)

        new_name = changes.get("name")
        if new_name is not None:
            clash = self._cells.get_by_name(new_name)
            if clash is not None and clash.id != cell.id:
                raise DuplicateCellNameError(new_name)

        new_rated = changes.get("rated_voltage")
        if new_rated is not None:
            changes["max_safe_voltage"] = safe_voltage_limit(new_rated)

        return CellOut.model_validate(self._cells.apply_changes(cell, changes))

    def delete(self, cell_id: int) -> None:
        self._cells.delete(self._require_cell(cell_id))

    def _require_cell(self, cell_id: int) -> PhotovoltaicCell:
        cell = self._cells.get_by_id(cell_id)
        if cell is None:
            raise CellNotFoundError(cell_id)
        return cell
