"""Integración de FastAPI con la dependencia de sesión y PostgreSQL."""

from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import session as session_module
from app.db.health import check_database_connection
from app.db.safety import database_name
from app.db.session import get_db


class TrackingSession(Session):
    """Sesión que registra si la dependencia la cerró."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.was_closed = False

    def close(self) -> None:
        self.was_closed = True
        super().close()


def build_probe_app() -> FastAPI:
    """Aplicación mínima de prueba; no añade rutas a la app real."""
    probe_app = FastAPI()

    @probe_app.get("/__test__/db")
    def db_probe(db: Session = Depends(get_db)) -> dict[str, bool]:
        return {"connected": check_database_connection(db)}

    return probe_app


@pytest.mark.integration
def test_fastapi_can_connect_and_close_a_session(
    monkeypatch: pytest.MonkeyPatch,
    test_engine: Engine,
) -> None:
    created: list[TrackingSession] = []

    def session_factory() -> TrackingSession:
        session = TrackingSession(bind=test_engine)
        created.append(session)
        return session

    monkeypatch.setattr(session_module, "SessionLocal", session_factory)

    app = build_probe_app()
    with TestClient(app) as client:
        response = client.get("/__test__/db")

    assert response.status_code == 200
    assert response.json() == {"connected": True}
    assert created
    assert created[0].was_closed is True


@pytest.mark.integration
def test_runtime_settings_use_separate_databases() -> None:
    assert settings.test_database_url is not None
    assert settings.test_database_url != settings.database_url
    assert database_name(settings.database_url) == "nexora_dev"
    assert database_name(settings.test_database_url) == "nexora_test"
