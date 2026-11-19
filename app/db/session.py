"""Configuración de la conexión y de las sesiones de SQLAlchemy."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.safety import database_name

DEFAULT_CONNECT_TIMEOUT_SECONDS = 5


def create_database_engine(
    database_url: str,
    forbidden: frozenset[str] | None = None,
    **kwargs: Any,
) -> Engine:
    """Crea un engine síncrono de SQLAlchemy para PostgreSQL.

    Se aplica un timeout de conexión por defecto para que un fallo de red
    no deje la petición esperando indefinidamente. Puede sobrescribirse
    mediante ``connect_args``. Las bases reservadas se rechazan también
    en este punto como defensa adicional.
    """
    if forbidden is None:
        forbidden = settings.forbidden_database_names
    if database_name(database_url) in forbidden:
        raise ValueError(
            "La base de datos indicada está reservada y no puede utilizarse."
        )

    options: dict[str, Any] = {"pool_pre_ping": True}
    connect_args = dict(kwargs.pop("connect_args", {}) or {})
    connect_args.setdefault("connect_timeout", DEFAULT_CONNECT_TIMEOUT_SECONDS)
    options["connect_args"] = connect_args
    options.update(kwargs)
    return create_engine(database_url, **options)


def create_session_factory(engine: Engine) -> sessionmaker:
    """Crea una fábrica de sesiones ligada al engine indicado."""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


engine = create_database_engine(settings.database_url)
SessionLocal = create_session_factory(engine)


def get_db() -> Generator[Session, None, None]:
    """Proporciona una sesión y la cierra siempre al terminar.

    Los servicios son responsables de confirmar la transacción. Si una
    excepción alcanza esta dependencia, se revierte la transacción y se
    propaga el error. No se aplica autocommit.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
