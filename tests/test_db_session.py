"""Pruebas de las sesiones de base de datos (SQLAlchemy) y de las protecciones.

No son las sesiones de usuario (inicio de sesión), que llegarán con ADR-0008.
"""

from typing import Any

import pytest
from sqlalchemy import text

from app.core.config import FORBIDDEN_DATABASE_NAMES
from app.core.errors import DatabaseConnectionError
from app.db import session as session_module
from app.db.health import check_database_connection, verify_engine_connection
from app.db.safety import UnsafeDatabaseError, assert_safe_test_database
from app.db.session import create_database_engine, get_db

DEV_URL = "postgresql+psycopg://nexora@localhost:5432/nexora_dev"
TEST_URL = "postgresql+psycopg://nexora@localhost:5432/nexora_test"


class FakeSession:
    """Sesión mínima para comprobar el ciclo de vida sin base de datos."""

    def __init__(self) -> None:
        self.closed = False
        self.rolled_back = False

    def close(self) -> None:
        self.closed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_get_db_closes_the_session(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeSession()
    monkeypatch.setattr(session_module, "SessionLocal", lambda: fake)

    generator = get_db()
    assert next(generator) is fake

    generator.close()

    assert fake.closed is True
    assert fake.rolled_back is False


def test_get_db_rolls_back_and_closes_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeSession()
    monkeypatch.setattr(session_module, "SessionLocal", lambda: fake)

    generator = get_db()
    assert next(generator) is fake

    with pytest.raises(RuntimeError, match="fallo controlado"):
        generator.throw(RuntimeError("fallo controlado"))

    assert fake.rolled_back is True
    assert fake.closed is True


@pytest.mark.integration
def test_engine_can_connect_and_run_select_one(test_engine: Any) -> None:
    assert test_engine.url.database == "nexora_test"
    assert verify_engine_connection(test_engine) is True


@pytest.mark.integration
def test_session_can_run_select_one(test_session: Any) -> None:
    assert test_session.get_bind().url.database == "nexora_test"
    assert check_database_connection(test_session) is True


@pytest.mark.integration
def test_get_db_yields_a_working_session(
    monkeypatch: pytest.MonkeyPatch,
    test_session_factory: Any,
) -> None:
    monkeypatch.setattr(session_module, "SessionLocal", test_session_factory)

    generator = get_db()
    db = next(generator)
    try:
        assert db.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        generator.close()


@pytest.mark.integration
def test_session_factory_opens_and_closes_a_session(test_session_factory: Any) -> None:
    session = test_session_factory()
    try:
        assert check_database_connection(session) is True
    finally:
        session.close()


def test_connection_failure_is_controlled_and_does_not_leak_details() -> None:
    failing_engine = create_database_engine(
        "postgresql+psycopg://nexora@127.0.0.1:1/nexora_test",
    )
    try:
        with pytest.raises(DatabaseConnectionError) as error:
            verify_engine_connection(failing_engine)
    finally:
        failing_engine.dispose()

    message = str(error.value)
    assert "postgresql" not in message.lower()
    assert "nexora" not in message.lower()
    assert "127.0.0.1" not in message


def test_engine_refuses_reserved_databases() -> None:
    for database in sorted(FORBIDDEN_DATABASE_NAMES):
        with pytest.raises(ValueError):
            create_database_engine(
                f"postgresql+psycopg://nexora@localhost:5432/{database}"
            )


def test_engine_refuses_databases_of_the_local_denylist() -> None:
    with pytest.raises(ValueError):
        create_database_engine(
            "postgresql+psycopg://nexora@localhost:5432/otra_base",
            forbidden=frozenset({"otra_base"}),
        )


def test_guard_rejects_databases_of_the_local_denylist() -> None:
    with pytest.raises(UnsafeDatabaseError):
        assert_safe_test_database(
            TEST_URL,
            DEV_URL,
            forbidden=frozenset({"nexora_test"}),
        )


def test_guard_accepts_nexora_test() -> None:
    assert_safe_test_database(TEST_URL, DEV_URL)


@pytest.mark.parametrize("database", sorted(FORBIDDEN_DATABASE_NAMES))
def test_guard_rejects_reserved_databases(database: str) -> None:
    with pytest.raises(UnsafeDatabaseError):
        assert_safe_test_database(
            f"postgresql+psycopg://nexora@localhost:5432/{database}",
            DEV_URL,
        )


def test_guard_rejects_a_test_database_with_another_name() -> None:
    with pytest.raises(UnsafeDatabaseError):
        assert_safe_test_database(
            "postgresql+psycopg://nexora@localhost:5432/nexora_test_extra",
            DEV_URL,
        )


def test_guard_rejects_the_development_database_as_test() -> None:
    with pytest.raises(UnsafeDatabaseError):
        assert_safe_test_database(TEST_URL, TEST_URL)
