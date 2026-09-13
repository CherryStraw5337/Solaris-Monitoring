from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base, UTCDateTime
from utils.clock import utc_now

if TYPE_CHECKING:
    from utils.models.photovoltaic_cell import PhotovoltaicCell


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    cell_id: Mapped[int] = mapped_column(
        ForeignKey("photovoltaic_cells.id", ondelete="CASCADE"), index=True
    )
    voltage_measured: Mapped[float] = mapped_column(Float)
    efficiency_percentage: Mapped[float] = mapped_column(Float)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime, index=True, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    cell: Mapped[PhotovoltaicCell] = relationship(back_populates="readings")
