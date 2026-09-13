import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
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

# Security scheme para Swagger
api_key_header = APIKeyHeader(name="X-API-Key", description="API Key para escribir datos")


def verify_api_key(
    x_api_key: str = Depends(api_key_header),
) -> str:
    """Verifica que la clave API proporcionada sea correcta.

    Usa secrets.compare_digest para evitar timing attacks.

    Args:
        x_api_key: El valor del header X-API-Key

    Returns:
        La clave si es válida

    Raises:
        HTTPException: 401 si la clave es inválida o no está configurada
    """
    from main import get_settings

    settings = get_settings()

    if not settings.device_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key no configurada en el servidor",
        )

    # Comparar de forma segura contra timing attacks
    if not secrets.compare_digest(x_api_key, settings.device_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida",
        )

    return x_api_key


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
