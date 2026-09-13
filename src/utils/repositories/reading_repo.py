from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from utils.models import Reading


class SqlAlchemyReadingRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, reading: Reading) -> Reading:
        self._db.add(reading)
        self._db.commit()
        self._db.refresh(reading)
        return reading

    def get_by_id(self, reading_id: int) -> Reading | None:
        return self._db.get(Reading, reading_id)

    def list_all(self, limit: int) -> list[Reading]:
        statement = select(Reading).order_by(Reading.timestamp.desc(), Reading.id.desc())
        return list(self._db.scalars(statement.limit(limit)))

    def list_by_cell(self, cell_id: int, limit: int) -> list[Reading]:
        statement = (
            select(Reading)
            .where(Reading.cell_id == cell_id)
            .order_by(Reading.timestamp.desc(), Reading.id.desc())
            .limit(limit)
        )
        return list(self._db.scalars(statement))

    def list_since(self, cell_id: int, since: datetime) -> list[Reading]:
        statement = (
            select(Reading)
            .where(Reading.cell_id == cell_id, Reading.timestamp >= since)
            .order_by(Reading.timestamp.desc(), Reading.id.desc())
        )
        return list(self._db.scalars(statement))
