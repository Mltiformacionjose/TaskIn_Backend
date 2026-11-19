"""Pruebas del modelo User frente a la tabla users del modelo de datos v0.6."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User

TABLE = User.__table__


def make_user(**overrides: object) -> User:
    values: dict[str, object] = {
        "username": "ana",
        "email": "ana@example.com",
        "password_hash": "hash-de-prueba",
    }
    values.update(overrides)
    return User(**values)


# ---------- Estructura (sin base de datos)


def test_columns_match_the_reference_sql() -> None:
    expected = {
        "id": (False,),
        "username": (False, String, 50),
        "email": (False, String, 255),
        "password_hash": (False, String, 255),
        "notifications_enabled": (False, Boolean),
        "reset_token_hash": (True, String, 255),
        "reset_expires_at": (True, DateTime),
        "created_at": (False, DateTime),
    }
    assert list(TABLE.columns.keys()) == list(expected)
    for name, (nullable, *kind) in expected.items():
        column = TABLE.columns[name]
        assert column.nullable is nullable, name
        if kind:
            assert isinstance(column.type, kind[0]), name
        if len(kind) == 2:
            assert column.type.length == kind[1], name


def test_dates_are_timestamptz() -> None:
    for name in ("reset_expires_at", "created_at"):
        assert TABLE.columns[name].type.timezone is True


def test_id_is_identity_by_default() -> None:
    identity = TABLE.columns["id"].identity
    assert identity is not None
    assert identity.always is False


def test_constraint_and_index_names_match_the_reference_sql() -> None:
    names = {c.name for c in TABLE.constraints}
    assert {"users_pkey", "ck_users_reset", "users_reset_token_hash_key"} <= names
    indexes = {i.name: i.unique for i in TABLE.indexes}
    assert indexes == {"uq_users_username": True, "uq_users_email": True}


# ---------- Comportamiento en PostgreSQL (nexora_test, esquema temporal)


@pytest.mark.integration
def test_insert_applies_server_defaults(model_session: Session) -> None:
    user = make_user()
    model_session.add(user)
    model_session.flush()
    model_session.refresh(user)

    assert user.id is not None
    assert user.notifications_enabled is True
    assert user.created_at is not None
    assert user.reset_token_hash is None


@pytest.mark.integration
@pytest.mark.parametrize(
    "duplicate",
    [
        {"username": "ANA", "email": "otra@example.com"},
        {"username": "otra", "email": "Ana@Example.com"},
    ],
    ids=["username", "email"],
)
def test_username_and_email_are_unique_ignoring_case(
    model_session: Session,
    duplicate: dict[str, str],
) -> None:
    model_session.add(make_user())
    model_session.flush()

    model_session.add(make_user(**duplicate))
    with pytest.raises(IntegrityError, match="uq_users_"):
        model_session.flush()


@pytest.mark.integration
@pytest.mark.parametrize(
    "reset",
    [
        {"reset_token_hash": "token"},
        {"reset_expires_at": datetime.now(UTC)},
    ],
    ids=["token-sin-caducidad", "caducidad-sin-token"],
)
def test_reset_token_and_expiry_go_together(
    model_session: Session,
    reset: dict[str, object],
) -> None:
    model_session.add(make_user(**reset))
    with pytest.raises(IntegrityError, match="ck_users_reset"):
        model_session.flush()


@pytest.mark.integration
def test_reset_token_hash_is_unique(model_session: Session) -> None:
    expires = datetime.now(UTC) + timedelta(hours=1)
    model_session.add(make_user(reset_token_hash="t", reset_expires_at=expires))
    model_session.add(
        make_user(
            username="otra",
            email="otra@example.com",
            reset_token_hash="t",
            reset_expires_at=expires,
        )
    )
    with pytest.raises(IntegrityError, match="users_reset_token_hash_key"):
        model_session.flush()


@pytest.mark.integration
def test_required_fields_cannot_be_null(model_session: Session) -> None:
    model_session.add(make_user(password_hash=None))
    with pytest.raises(IntegrityError):
        model_session.flush()
