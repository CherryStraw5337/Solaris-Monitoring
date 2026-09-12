from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from edsia_beyond.domain.errors import (
    CellNotFoundError,
    DomainError,
    DuplicateCellNameError,
    InactiveCellError,
    NoReadingsInPeriodError,
    ReadingNotFoundError,
)

# La búsqueda es por tipo exacto: una subclase no mapeada cae al 400 por defecto.
STATUS_BY_ERROR: dict[type[Exception], int] = {
    CellNotFoundError: status.HTTP_404_NOT_FOUND,
    ReadingNotFoundError: status.HTTP_404_NOT_FOUND,
    NoReadingsInPeriodError: status.HTTP_404_NOT_FOUND,
    DuplicateCellNameError: status.HTTP_409_CONFLICT,
    InactiveCellError: status.HTTP_409_CONFLICT,
}


def register_exception_handlers(app: FastAPI) -> None:
    async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
        status_code = STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    app.add_exception_handler(DomainError, handle_domain_error)
