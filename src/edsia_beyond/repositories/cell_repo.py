from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from edsia_beyond.models import PhotovoltaicCell


class SqlAlchemyCellRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, cell: PhotovoltaicCell) -> PhotovoltaicCell:
        self._db.add(cell)
        self._db.commit()
        self._db.refresh(cell)
        return cell

    def get_by_id(self, cell_id: int) -> PhotovoltaicCell | None:
        return self._db.get(PhotovoltaicCell, cell_id)

    def get_by_name(self, name: str) -> PhotovoltaicCell | None:
        return self._db.scalar(select(PhotovoltaicCell).where(PhotovoltaicCell.name == name))

    def list_all(self) -> list[PhotovoltaicCell]:
        return list(self._db.scalars(select(PhotovoltaicCell).order_by(PhotovoltaicCell.id)))

    def list_active(self) -> list[PhotovoltaicCell]:
        statement = (
            select(PhotovoltaicCell)
            .where(PhotovoltaicCell.is_active.is_(True))
            .order_by(PhotovoltaicCell.id)
        )
        return list(self._db.scalars(statement))

    def apply_changes(
        self, cell: PhotovoltaicCell, changes: Mapping[str, Any]
    ) -> PhotovoltaicCell:
        for field, value in changes.items():
            setattr(cell, field, value)
        self._db.commit()
        self._db.refresh(cell)
        return cell

    def delete(self, cell: PhotovoltaicCell) -> None:
        self._db.delete(cell)
        self._db.commit()
