"""Verificaciones de conectividad con PostgreSQL."""

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import DatabaseConnectionError


def _select_one(executor: Session | Connection) -> bool:
    try:
        result = executor.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError() from exc
    return result == 1


def check_database_connection(session: Session) -> bool:
    """Ejecuta ``SELECT 1`` en una sesión y valida el resultado."""
    return _select_one(session)


def verify_engine_connection(engine: Engine) -> bool:
    """Adquiere una conexión del engine, ejecuta ``SELECT 1`` y la cierra."""
    try:
        with engine.connect() as connection:
            return _select_one(connection)
    except DatabaseConnectionError:
        raise
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError() from exc
