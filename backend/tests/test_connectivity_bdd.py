"""Pasos Gherkin del escenario de conectividad con PostgreSQL."""

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy.orm import Session

from app.db.health import check_database_connection, verify_engine_connection
from app.db.safety import database_name

pytestmark = pytest.mark.integration

scenarios("features/connectivity.feature")


@given("que PostgreSQL está disponible")
def postgresql_is_available(test_engine: object) -> None:
    assert verify_engine_connection(test_engine) is True


@given("el backend tiene configurada una conexión válida")
def backend_has_a_valid_connection(test_database_url: str) -> None:
    assert database_name(test_database_url) == "nexora_test"


@pytest.fixture()
def open_test_session(test_session_factory: object) -> Session:
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@when("el backend solicita una conexión")
def backend_requests_a_connection(
    open_test_session: Session,
    bdd_context: dict[str, object],
) -> None:
    bdd_context["session"] = open_test_session


@then("la conexión se establece correctamente")
def connection_is_established(bdd_context: dict[str, object]) -> None:
    session = bdd_context["session"]
    assert isinstance(session, Session)
    assert session.is_active is True


@then("la consulta SELECT 1 devuelve un resultado válido")
def select_one_returns_a_valid_result(bdd_context: dict[str, object]) -> None:
    session = bdd_context["session"]
    assert isinstance(session, Session)
    assert check_database_connection(session) is True
