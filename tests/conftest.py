"""Fixtures comunes de las pruebas del backend."""

import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, text
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
            "TEST_DATABASE_URL no está configurada. Copia .env.example "
            "a .env y apunta a nexora_test."
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


@pytest.fixture(scope="session")
def model_schema(test_engine: Engine) -> Generator[Engine, None, None]:
    """Crea las tablas de los modelos en un esquema temporal de nexora_test.

    Así las pruebas de modelos no dependen de las migraciones ni dejan
    tablas en el esquema public. El esquema se borra siempre al terminar.
    """
    from app.db.base import Base
    import app.models  # noqa: F401  (registra las tablas en Base.metadata)

    schema = f"test_models_{uuid.uuid4().hex[:8]}"
    engine = test_engine.execution_options(schema_translate_map={None: schema})
    with test_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        with engine.begin() as connection:
            Base.metadata.create_all(connection)
        yield engine
    finally:
        with test_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


@pytest.fixture()
def model_session(model_schema: Engine) -> Generator[Session, None, None]:
    """Sesión sobre el esquema temporal; todo se deshace al terminar."""
    connection = model_schema.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
