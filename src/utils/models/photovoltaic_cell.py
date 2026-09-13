from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base

if TYPE_CHECKING:
    from utils.models.reading import Reading


class PhotovoltaicCell(Base):
    __tablename__ = "photovoltaic_cells"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    location: Mapped[str] = mapped_column(String(200))
    rated_voltage: Mapped[float] = mapped_column(Float)
    max_safe_voltage: Mapped[float] = mapped_column(Float)
    efficiency_threshold: Mapped[float] = mapped_column(Float, default=80.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Sin passive_deletes: SQLite no aplica FK por defecto, así que el borrado en
    # cascada lo resuelve el ORM y funciona igual en SQLite y PostgreSQL.
    readings: Mapped[list[Reading]] = relationship(
        back_populates="cell",
        cascade="all, delete-orphan",
    )
