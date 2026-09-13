from pydantic import BaseModel, ConfigDict, Field


class CellCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    rated_voltage: float = Field(..., gt=0)
    efficiency_threshold: float = Field(default=80.0, ge=0, le=100)


class CellUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=200)
    rated_voltage: float | None = Field(default=None, gt=0)
    efficiency_threshold: float | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class CellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    rated_voltage: float
    max_safe_voltage: float
    efficiency_threshold: float
    is_active: bool
