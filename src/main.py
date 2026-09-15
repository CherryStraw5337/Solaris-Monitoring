import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import SessionLocal
from utils.config import Settings
from utils.exception_handlers import register_exception_handlers
from utils.mqtt_adapter import MQTTAdapter
from utils.routers import cells, health, readings

API_PREFIX = "/api/v1"
PUBLIC_DIR = Path(__file__).resolve().parent / "public"

# Almacenar Settings globalmente para usarlo en dependencias
_current_settings: Settings | None = None
_mqtt_adapter: MQTTAdapter | None = None


def get_settings() -> Settings:
    """Dependencia que retorna la configuración actual."""
    global _current_settings
    if _current_settings is None:
        _current_settings = Settings.from_env()
    return _current_settings


def get_mqtt_adapter() -> MQTTAdapter | None:
    """Obtiene la instancia del adaptador MQTT."""
    return _mqtt_adapter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage FastAPI lifespan events: startup and shutdown.

    Starts MQTT adapter connection in a background thread on startup.
    Gracefully stops MQTT connection on shutdown.
    """
    global _mqtt_adapter

    # Startup
    settings = get_settings()
    _mqtt_adapter = MQTTAdapter(settings, SessionLocal)

    if _mqtt_adapter.enabled:
        # Run MQTT connection in background thread (non-blocking)
        mqtt_thread = threading.Thread(target=_mqtt_adapter.connect, daemon=True)
        mqtt_thread.start()
        print("🟢 MQTT adapter started in background thread")
    else:
        print("⚪ MQTT adapter disabled (MQTT_HOST not configured)")

    yield

    # Shutdown
    if _mqtt_adapter:
        _mqtt_adapter.disconnect()
        print("🔴 MQTT adapter disconnected")


def create_app(settings: Settings | None = None) -> FastAPI:
    global _current_settings
    resolved = settings if settings is not None else Settings.from_env()
    _current_settings = resolved

    app = FastAPI(
        title=resolved.api_title,
        description="API REST para monitoreo de eficiencia de celdas fotovoltaicas",
        version=resolved.api_version,
        lifespan=lifespan,
    )
    # allow_credentials debe ser False mientras el origen sea comodín: el navegador
    # rechaza la combinación "*" + credenciales.
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
    # Debe montarse al final: un mount en "/" captura toda ruta no registrada antes.
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="landing")
    return app


app = create_app()
