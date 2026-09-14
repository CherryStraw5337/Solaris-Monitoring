from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import engine  # Importa el engine de la base de datos
from utils.config import Settings
from utils.exception_handlers import register_exception_handlers
from utils.models import Base  # Importa la base de modelos SQLAlchemy
from utils.mqtt_listener import start_mqtt_client
from utils.routers import cells, health, readings

API_PREFIX = "/api/v1"
PUBLIC_DIR = Path(__file__).resolve().parent / "public"

_current_settings: Settings | None = None


def get_settings() -> Settings:
    """Dependencia que retorna la configuración actual."""
    global _current_settings
    if _current_settings is None:
        _current_settings = Settings.from_env()
    return _current_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    global _current_settings
    resolved = settings if settings is not None else Settings.from_env()
    _current_settings = resolved

    app = FastAPI(
        title=resolved.api_title,
        description="API REST y MQTT para monitoreo de eficiencia de celdas fotovoltaicas",
        version=resolved.api_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(cells.router, prefix=API_PREFIX)
    app.include_router(readings.router, prefix=API_PREFIX)

    @app.on_event("startup")
    def startup_event() -> None:
        # Crea las tablas automáticamente (soluciona el error de "no such table")
        Base.metadata.create_all(bind=engine)
        # Arranca tu listener MQTT en segundo plano
        start_mqtt_client()

    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="landing")
    return app


app = create_app()
