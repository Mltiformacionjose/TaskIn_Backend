"""Comprobación manual de la conexión con PostgreSQL.

No expone ningún endpoint HTTP: se ejecuta como comando interno.

    python -m app.db.check
    python -m app.db.check --test
"""

import argparse
import sys

from sqlalchemy import Engine

from app.core.config import settings
from app.core.errors import DatabaseConnectionError
from app.db.health import verify_engine_connection
from app.db.safety import UnsafeDatabaseError, assert_safe_test_database
from app.db.session import create_database_engine, engine


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica la conexión de TaskIn con PostgreSQL mediante SELECT 1."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Comprueba TEST_DATABASE_URL (nexora_test) en lugar de DATABASE_URL.",
    )
    args = parser.parse_args()

    target = "pruebas" if args.test else "desarrollo"
    selected_engine: Engine = engine

    if args.test:
        if not settings.test_database_url:
            print(
                "TEST_DATABASE_URL no está configurada.",
                file=sys.stderr,
            )
            return 2
        try:
            assert_safe_test_database(
                settings.test_database_url,
                settings.database_url,
            )
        except UnsafeDatabaseError as exc:
            print(f"Configuración de pruebas rechazada: {exc}", file=sys.stderr)
            return 2
        selected_engine = create_database_engine(settings.test_database_url)

    try:
        verify_engine_connection(selected_engine)
    except DatabaseConnectionError as exc:
        print(f"Error de conexión ({target}): {exc}", file=sys.stderr)
        return 1
    finally:
        if args.test:
            selected_engine.dispose()

    print(f"Conexión correcta con PostgreSQL ({target}): SELECT 1 = 1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
