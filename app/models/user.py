"""Tabla users: cuenta de una persona registrada (modelo de datos v0.6).

La recuperación de contraseña vive aquí: un único enlace activo por persona.
Pedir otro sustituye al anterior y usarlo deja reset_* a NULL. El nombre de
usuario y el correo son únicos sin distinguir mayúsculas (índices sobre
lower()).
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Identity,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    reset_token_hash: Mapped[str | None] = mapped_column(String(255), unique=True)
    reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "(reset_token_hash IS NULL) = (reset_expires_at IS NULL)",
            name="ck_users_reset",
        ),
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"


Index("uq_users_username", func.lower(User.username), unique=True)
Index("uq_users_email", func.lower(User.email), unique=True)
