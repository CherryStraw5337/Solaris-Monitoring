from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "sqlite:///./edsia_beyond.db"
DEFAULT_API_TITLE = "EDSIA Beyond - Photovoltaic Monitor"
DEFAULT_API_VERSION = "1.0.0"


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
            database_url=source.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            environment=source.get("ENVIRONMENT", "development"),
            api_title=source.get("API_TITLE", DEFAULT_API_TITLE),
            api_version=source.get("API_VERSION", DEFAULT_API_VERSION),
        )
