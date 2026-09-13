from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LecturaPanel(Base):
    __tablename__ = "lecturas_panel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    voltaje: Mapped[float] = mapped_column(Float, nullable=False)
    corriente: Mapped[float] = mapped_column(Float, nullable=False)
    potencia: Mapped[float] = mapped_column(Float, nullable=False)
    energia_acumulada: Mapped[float] = mapped_column(Float, nullable=False)
    punto_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
