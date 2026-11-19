"""Modelos ORM de SQLAlchemy (modelo de datos v0.6).

Se importan aquí para que Base.metadata conozca todas las tablas.
Se añaden de una en una; user_sessions espera a ADR-0008.
"""

from app.models.user import User

__all__ = ["User"]
