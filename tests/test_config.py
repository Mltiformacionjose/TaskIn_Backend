"""Pruebas de la configuración leída desde variables de entorno."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import (
    FORBIDDEN_DATABASE_NAMES,
    TEST_DATABASE_NAME,
    Settings,
)

DEV_URL = "postgresql+psycopg://nexora@localhost:5432/nexora_dev"
TEST_URL = "postgresql+psycopg://nexora@localhost:5432/nexora_test"
ENV_EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"


@pytest.fixture(autouse=True)
def clean_database_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (
        "DATABASE_URL",
        "TEST_DATABASE_URL",
        "FRONTEND_ORIGIN",
        "DATABASE_DENYLIST",
    ):
        monkeypatch.delenv(variable, raising=False)


def build_settings(
    monkeypatch: pytest.MonkeyPatch,
    **values: Any,
) -> Settings:
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def read_env_example() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values


def test_settings_reads_database_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    configured = build_settings(
        monkeypatch,
        DATABASE_URL=DEV_URL,
        TEST_DATABASE_URL=TEST_URL,
    )

    assert configured.database_url == DEV_URL
    assert configured.test_database_url == TEST_URL
    assert configured.frontend_origin == "http://localhost:3000"


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError):
        build_settings(monkeypatch)


def test_test_database_url_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    configured = build_settings(monkeypatch, DATABASE_URL=DEV_URL)

    assert configured.test_database_url is None


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///nexora.db",
        "mysql+pymysql://nexora@localhost:3306/nexora_dev",
    ],
)
def test_rejects_urls_that_are_not_postgresql_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    with pytest.raises(ValidationError):
        build_settings(monkeypatch, DATABASE_URL=url)


@pytest.mark.parametrize("database", sorted(FORBIDDEN_DATABASE_NAMES))
def test_rejects_reserved_databases(
    monkeypatch: pytest.MonkeyPatch,
    database: str,
) -> None:
    with pytest.raises(ValidationError):
        build_settings(
            monkeypatch,
            DATABASE_URL=f"postgresql+psycopg://nexora@localhost:5432/{database}",
        )


@pytest.mark.parametrize("database", sorted(FORBIDDEN_DATABASE_NAMES))
def test_rejects_reserved_test_databases(
    monkeypatch: pytest.MonkeyPatch,
    database: str,
) -> None:
    with pytest.raises(ValidationError):
        build_settings(
            monkeypatch,
            DATABASE_URL=DEV_URL,
            TEST_DATABASE_URL=(
                f"postgresql+psycopg://nexora@localhost:5432/{database}"
            ),
        )


DENYLIST = "otra_base, otra_base_test ,"


def test_denylist_is_empty_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    configured = build_settings(monkeypatch, DATABASE_URL=DEV_URL)

    assert configured.forbidden_database_names == FORBIDDEN_DATABASE_NAMES


def test_denylist_adds_local_databases(monkeypatch: pytest.MonkeyPatch) -> None:
    configured = build_settings(
        monkeypatch,
        DATABASE_URL=DEV_URL,
        DATABASE_DENYLIST=DENYLIST,
    )

    assert configured.forbidden_database_names == FORBIDDEN_DATABASE_NAMES | {
        "otra_base",
        "otra_base_test",
    }


@pytest.mark.parametrize("database", ["otra_base", "otra_base_test"])
def test_rejects_denylisted_development_database(
    monkeypatch: pytest.MonkeyPatch,
    database: str,
) -> None:
    with pytest.raises(ValidationError):
        build_settings(
            monkeypatch,
            DATABASE_URL=f"postgresql+psycopg://nexora@localhost:5432/{database}",
            DATABASE_DENYLIST=DENYLIST,
        )


def test_rejects_denylisted_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError):
        build_settings(
            monkeypatch,
            DATABASE_URL=DEV_URL,
            TEST_DATABASE_URL=TEST_URL,
            DATABASE_DENYLIST="nexora_test",
        )


def test_rejects_test_database_with_another_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValidationError):
        build_settings(
            monkeypatch,
            DATABASE_URL=DEV_URL,
            TEST_DATABASE_URL=(
                "postgresql+psycopg://nexora@localhost:5432/nexora_test_extra"
            ),
        )


def test_rejects_test_database_equal_to_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValidationError):
        build_settings(
            monkeypatch,
            DATABASE_URL=TEST_URL,
            TEST_DATABASE_URL=TEST_URL,
        )


def test_env_example_documents_separate_databases_without_real_secrets() -> None:
    values = read_env_example()

    assert values["DATABASE_URL"].endswith("/nexora_dev")
    assert values["TEST_DATABASE_URL"].endswith(f"/{TEST_DATABASE_NAME}")
    assert "USER:PASSWORD" in values["DATABASE_URL"]
    assert "USER:PASSWORD" in values["TEST_DATABASE_URL"]
    assert "FRONTEND_ORIGIN" in values
    assert values["DATABASE_DENYLIST"] == ""
