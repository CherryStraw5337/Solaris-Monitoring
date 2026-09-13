from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "sqlite:///./db"
DEFAULT_API_TITLE = "Solaris Monitoring - Photovoltaic Monitor"
DEFAULT_API_VERSION = "1.0.0"

# Render y otros proveedores entregan "postgres://" o "postgresql://" sin driver;
# SQLAlchemy asume psycopg2, pero el proyecto instala psycopg (v3).
_BARE_POSTGRES_SCHEMES = ("postgres://", "postgresql://")
_PSYCOPG_SCHEME = "postgresql+psycopg://"


def normalize_database_url(url: str) -> str:
    for scheme in _BARE_POSTGRES_SCHEMES:
        if url.startswith(scheme):
            return _PSYCOPG_SCHEME + url[len(scheme) :]
    return url


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    environment: str = "development"
    api_title: str = DEFAULT_API_TITLE
    api_version: str = DEFAULT_API_VERSION
    device_api_key: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source: Mapping[str, str] = os.environ if env is None else env
        environment = source.get("ENVIRONMENT", "development")
        device_api_key = source.get("DEVICE_API_KEY")

        # En producción, la clave es obligatoria
        if environment == "production" and not device_api_key:
            msg = (
                "DEVICE_API_KEY no está definida. En producción, debe configurarse como "
                "variable de entorno secreta. Revisa docs/DEPLOYMENT.md para más información."
            )
            raise ValueError(msg)

        return cls(
            database_url=normalize_database_url(source.get("DATABASE_URL", DEFAULT_DATABASE_URL)),
            environment=environment,
            api_title=source.get("API_TITLE", DEFAULT_API_TITLE),
            api_version=source.get("API_VERSION", DEFAULT_API_VERSION),
            device_api_key=device_api_key,
        )
