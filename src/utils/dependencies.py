from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from db import get_db
from utils.domain.analysis import (
    CompositeAnomalyDetector,
    LowEfficiencyAnomalyDetector,
    OverVoltageAnomalyDetector,
    RatioEfficiencyCalculator,
    ReadingAnalyzer,
)
from utils.repositories.cell_repo import SqlAlchemyCellRepository
from utils.repositories.reading_repo import SqlAlchemyReadingRepository
from utils.services.cell_service import CellService
from utils.services.reading_service import ReadingService

DbSession = Annotated[Session, Depends(get_db)]


def build_reading_analyzer() -> ReadingAnalyzer:
    return ReadingAnalyzer(
        calculator=RatioEfficiencyCalculator(),
        detector=CompositeAnomalyDetector(
            [OverVoltageAnomalyDetector(), LowEfficiencyAnomalyDetector()]
        ),
    )


def get_cell_service(db: DbSession) -> CellService:
    return CellService(cells=SqlAlchemyCellRepository(db))


def get_reading_service(db: DbSession) -> ReadingService:
    return ReadingService(
        readings=SqlAlchemyReadingRepository(db),
        cells=SqlAlchemyCellRepository(db),
        analyzer=build_reading_analyzer(),
    )


CellServiceDep = Annotated[CellService, Depends(get_cell_service)]
ReadingServiceDep = Annotated[ReadingService, Depends(get_reading_service)]
