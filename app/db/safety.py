"""Protecciones para impedir que las pruebas usen bases de datos no permitidas."""

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.core.config import FORBIDDEN_DATABASE_NAMES, TEST_DATABASE_NAME


class UnsafeDatabaseError(RuntimeError):
    """La URL seleccionada no cumple las protecciones de BE-01."""


def database_name(database_url: str) -> str:
    """Devuelve el nombre exacto de la base de datos de una URL."""
    try:
        name = make_url(database_url).database
    except ArgumentError as exc:
        raise UnsafeDatabaseError("La URL de base de datos no es válida.") from exc
    if not name:
        raise UnsafeDatabaseError("La URL no incluye el nombre de la base de datos.")
    return name


def assert_safe_test_database(
    test_database_url: str,
    development_database_url: str,
) -> None:
    """Valida las protecciones obligatorias de la base de pruebas.

    - El nombre exacto debe ser ``nexora_test``.
    - No puede ser una de las bases reservadas del entorno local.
    - Debe ser distinta de la base de desarrollo.
    """
    test_name = database_name(test_database_url)
    development_name = database_name(development_database_url)

    if test_name in FORBIDDEN_DATABASE_NAMES:
        raise UnsafeDatabaseError(
            f"La base de pruebas '{test_name}' está reservada y no puede utilizarse."
        )
    if test_name != TEST_DATABASE_NAME:
        raise UnsafeDatabaseError(
            f"La base de pruebas debe llamarse exactamente '{TEST_DATABASE_NAME}'."
        )
    if (
        test_database_url == development_database_url
        or test_name == development_name
    ):
        raise UnsafeDatabaseError(
            "TEST_DATABASE_URL debe ser distinta de DATABASE_URL."
        )
