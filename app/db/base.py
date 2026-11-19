"""Base declarativa tipada de SQLAlchemy 2."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nombres de restricciones iguales a los que PostgreSQL pone por defecto
# al ejecutar el SQL de referencia del modelo v0.6. Los CHECK y los índices
# llevan su nombre explícito en cada modelo (ck_..., ix_..., uq_...).
NAMING_CONVENTION = {
    "pk": "%(table_name)s_pkey",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
}


class Base(DeclarativeBase):
    """Clase base para los modelos ORM de TaskIn."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
