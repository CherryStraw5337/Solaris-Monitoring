from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.config import Settings
from utils.exception_handlers import register_exception_handlers
from utils.routers import cells, health, readings

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings if settings is not None else Settings.from_env()
    app = FastAPI(
        title=resolved.api_title,
        description="API REST para monitoreo de eficiencia de celdas fotovoltaicas",
        version=resolved.api_version,
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
    return app


app = create_app()
