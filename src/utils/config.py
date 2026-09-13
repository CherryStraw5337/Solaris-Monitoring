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

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source: Mapping[str, str] = os.environ if env is None else env
        return cls(
            database_url=normalize_database_url(source.get("DATABASE_URL", DEFAULT_DATABASE_URL)),
            environment=source.get("ENVIRONMENT", "development"),
            api_title=source.get("API_TITLE", DEFAULT_API_TITLE),
            api_version=source.get("API_VERSION", DEFAULT_API_VERSION),
        )
