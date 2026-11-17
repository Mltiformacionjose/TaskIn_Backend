"""Comprobación mínima de infraestructura: la aplicación FastAPI importa."""

from fastapi import FastAPI

from app.main import app


def test_app_is_fastapi() -> None:
    assert isinstance(app, FastAPI)
