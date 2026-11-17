"""Base declarativa tipada de SQLAlchemy 2."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para los futuros modelos ORM de Nexora."""
