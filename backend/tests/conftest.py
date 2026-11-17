"""Fixtures comunes de las pruebas del backend."""

from collections.abc import Generator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.safety import UnsafeDatabaseError, assert_safe_test_database
from app.db.session import create_database_engine, create_session_factory


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """URL de pruebas validada contra las protecciones de BE-01."""
    url = settings.test_database_url
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL no está configurada. Copia backend/.env.example "
            "a backend/.env y apunta a nexora_test."
        )
    try:
        assert_safe_test_database(url, settings.database_url)
    except UnsafeDatabaseError as exc:
        pytest.fail(f"Configuración de pruebas rechazada: {exc}")
    return url


@pytest.fixture(scope="session")
def test_engine(test_database_url: str) -> Generator[Engine, None, None]:
    """Engine de integración ligado exclusivamente a nexora_test."""
    engine = create_database_engine(test_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def test_session_factory(test_engine: Engine) -> sessionmaker:
    return create_session_factory(test_engine)


@pytest.fixture()
def test_session(
    test_session_factory: sessionmaker,
) -> Generator[Session, None, None]:
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def bdd_context() -> dict[str, object]:
    """Contexto compartido entre los pasos Gherkin."""
    return {}
