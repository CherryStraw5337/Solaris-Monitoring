import os
from datetime import date

from fastapi import APIRouter

router = APIRouter(tags=["health"])


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
        # Render inyecta estas variables en cada deploy: permiten confirmar qué commit corre.
        "commit": os.environ.get("RENDER_GIT_COMMIT", "local"),
        "branch": os.environ.get("RENDER_GIT_BRANCH", "local"),
        "message": (
            "Solaris Monitoring API funcionando correctamente"
            if operational
            else "Solaris Monitoring API requiere atención: UPDATE_DATE no es válida"
        ),
    }
