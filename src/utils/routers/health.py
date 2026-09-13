import os
from datetime import date
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

PUBLIC_INDEX = Path(__file__).parents[1] / "public" / "index.html"

router = APIRouter(tags=["health"])


@router.get("/", response_class=FileResponse)
def root() -> FileResponse:
    return FileResponse(PUBLIC_INDEX)


@router.get("/health")
def health_check() -> dict[str, str]:
    configured_date = os.environ.get("UPDATE_DATE")
    if configured_date:
        try:
            update_date = date.fromisoformat(configured_date).isoformat()
        except ValueError:
            update_date = "Configuración inválida"
    else:
        update_date = "No definida"

    operational = update_date != "Configuración inválida"
    return {
        "status": "ok" if operational else "degraded",
        "service_status": "operational" if operational else "degraded",
        "update_date": update_date,
        "message": (
            "Solaris Monitoring API funcionando correctamente"
            if operational
            else "Solaris Monitoring API requiere atención: UPDATE_DATE no es válida"
        ),
    }
