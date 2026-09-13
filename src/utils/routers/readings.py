from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from utils.dependencies import ReadingServiceDep, verify_api_key
from utils.schemas.reading import ReadingCreate, ReadingOut, ReadingSummary

router = APIRouter(prefix="/readings", tags=["readings"])

LimitQuery = Annotated[int, Query(ge=1, le=1000)]
DaysQuery = Annotated[int, Query(ge=1, le=365)]
ApiKeyDep = Annotated[str, Depends(verify_api_key)]


@router.post("", response_model=ReadingOut, status_code=status.HTTP_201_CREATED)
def create_reading(payload: ReadingCreate, _: ApiKeyDep, service: ReadingServiceDep) -> ReadingOut:
    return service.create(payload)


@router.get("", response_model=list[ReadingOut])
def list_readings(service: ReadingServiceDep, limit: LimitQuery = 100) -> list[ReadingOut]:
    return service.list_all(limit)


@router.get("/cell/{cell_id}", response_model=list[ReadingOut])
def list_readings_by_cell(
    cell_id: int, service: ReadingServiceDep, limit: LimitQuery = 100
) -> list[ReadingOut]:
    return service.list_by_cell(cell_id, limit)


@router.get("/cell/{cell_id}/summary", response_model=ReadingSummary)
def get_cell_summary(
    cell_id: int, service: ReadingServiceDep, days: DaysQuery = 7
) -> ReadingSummary:
    return service.summary_for_cell(cell_id, days)


@router.get("/{reading_id}", response_model=ReadingOut)
def get_reading(reading_id: int, service: ReadingServiceDep) -> ReadingOut:
    return service.get(reading_id)
