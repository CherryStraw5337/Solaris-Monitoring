from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.clock import ensure_utc, utc_now

# Los relojes de un ESP32 sin RTC derivan; toleramos ese margen antes de rechazar.
CLOCK_SKEW_TOLERANCE = timedelta(minutes=5)


class ReadingCreate(BaseModel):
    cell_id: int = Field(..., gt=0)
    voltage_measured: float = Field(..., gt=0)
    timestamp: datetime | None = None

    @field_validator("timestamp")
    @classmethod
    def reject_future_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        normalized = ensure_utc(value)
        if normalized > utc_now() + CLOCK_SKEW_TOLERANCE:
            raise ValueError("timestamp cannot be in the future")
        return normalized


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cell_id: int
    voltage_measured: float
    efficiency_percentage: float
    is_anomaly: bool
    timestamp: datetime
    created_at: datetime


class ReadingSummary(BaseModel):
    cell_id: int
    cell_name: str
    period_days: int
    reading_count: int
    avg_voltage: float
    max_voltage: float
    min_voltage: float
    avg_efficiency: float
    anomaly_count: int
