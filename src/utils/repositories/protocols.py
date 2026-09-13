from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Protocol

from utils.models import PhotovoltaicCell, Reading


class CellLookup(Protocol):
    """Lo mínimo que necesita ReadingService: no debe ver operaciones de escritura."""

    def get_by_id(self, cell_id: int) -> PhotovoltaicCell | None: ...


class CellRepository(CellLookup, Protocol):
    def add(self, cell: PhotovoltaicCell) -> PhotovoltaicCell: ...

    def get_by_name(self, name: str) -> PhotovoltaicCell | None: ...

    def list_all(self) -> list[PhotovoltaicCell]: ...

    def list_active(self) -> list[PhotovoltaicCell]: ...

    def apply_changes(
        self, cell: PhotovoltaicCell, changes: Mapping[str, Any]
    ) -> PhotovoltaicCell: ...

    def delete(self, cell: PhotovoltaicCell) -> None: ...


class ReadingRepository(Protocol):
    def add(self, reading: Reading) -> Reading: ...

    def get_by_id(self, reading_id: int) -> Reading | None: ...

    def list_all(self, limit: int) -> list[Reading]: ...

    def list_by_cell(self, cell_id: int, limit: int) -> list[Reading]: ...

    def list_since(self, cell_id: int, since: datetime) -> list[Reading]: ...
