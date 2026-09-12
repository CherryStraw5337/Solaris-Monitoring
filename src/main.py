import os
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Solaris Monitoring", 
    description="API para monitoreo de métricas de paneles solares",
    version="0.1.0"
)

# Esquema Pydantic para validar los datos que envía el sensor_simulado.py
class LecturaPayload(BaseModel):
    timestamp: datetime
    voltaje: float
    corriente: float
    potencia: float
    energia_acumulada: float
    punto_id: int


def get_update_date() -> str:
    configured_date = os.getenv("UPDATE_DATE")
    if not configured_date:
        return "No definida"

    try:
        return datetime.strptime(configured_date, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return "Configuración inválida"


@app.get("/health")
def health_check() -> None:
    update_date = get_update_date()
    api_status = "operational" if update_date != "Configuración inválida" else "degraded"
    message = (
        "El sistema se encuentra en funcionamiento correcto"
        if api_status == "operational"
        else "El sistema requiere atención: la configuración de actualización no es válida"
    )

    return {
        "service_status": api_status,
        "update_date": update_date,
        "message": message,
    }

@app.post("/api/v1/lecturas")
def recibir_lectura(lectura: LecturaPayload) -> None:
    # TODO: Integrar inserción a la base de datos PostgreSQL con SQLAlchemy
    return {"message": "Lectura recibida exitosamente", "data": lectura}