import pytest

from utils.config import (
    DEFAULT_API_VERSION,
    DEFAULT_DATABASE_URL,
    Settings,
    normalize_database_url,
)


@pytest.mark.parametrize(
    "raw",
    [
        "postgres://u:p@host:5432/db",
        "postgresql://u:p@host:5432/db",
    ],
)
def test_bare_postgres_urls_use_the_psycopg3_driver(raw: str) -> None:
    assert normalize_database_url(raw) == "postgresql+psycopg://u:p@host:5432/db"


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://u:p@host:5432/db",
        "postgresql+asyncpg://u:p@host:5432/db",
        "sqlite:///./local.db",
    ],
)
def test_urls_with_explicit_driver_or_other_dialects_are_untouched(url: str) -> None:
    assert normalize_database_url(url) == url


def test_settings_normalize_the_database_url_from_the_environment() -> None:
    settings = Settings.from_env({"DATABASE_URL": "postgres://u:p@host:5432/db"})

    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_defaults_when_env_is_empty() -> None:
    settings = Settings.from_env({})

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.environment == "development"
    assert settings.api_version == DEFAULT_API_VERSION


def test_reads_values_from_provided_mapping() -> None:
    settings = Settings.from_env(
        {
            "DATABASE_URL": "postgresql+psycopg://u:p@host:5432/db",
            "ENVIRONMENT": "production",
            "API_TITLE": "Custom",
            "API_VERSION": "2.1.0",
        }
    )

    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"
    assert settings.environment == "production"
    assert settings.api_title == "Custom"
    assert settings.api_version == "2.1.0"


def test_falls_back_to_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///from-os-environ.db")

    assert Settings.from_env().database_url == "sqlite:///from-os-environ.db"


def test_settings_are_immutable() -> None:
    settings = Settings.from_env({})

    with pytest.raises(AttributeError):
        settings.environment = "staging"  # type: ignore[misc]
