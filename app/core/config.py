"""Configuración de la aplicación leída desde variables de entorno."""

from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

TEST_DATABASE_NAME = "nexora_test"

# Bases que nunca se usan, en cualquier equipo. Cada desarrollador puede
# bloquear otras bases de su entorno local con DATABASE_DENYLIST en .env
# (nombres separados por comas), sin escribirlas en el código.
FORBIDDEN_DATABASE_NAMES = frozenset({"postgres"})


def parse_denylist(value: str) -> frozenset[str]:
    """Convierte «base_a, base_b» en un conjunto de nombres sin espacios."""
    return frozenset(name.strip() for name in value.split(",") if name.strip())


class Settings(BaseSettings):
    """Variables de entorno; los ejemplos están en .env.example."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    test_database_url: str | None = None
    frontend_origin: str = "http://localhost:3000"
    database_denylist: str = ""

    @property
    def forbidden_database_names(self) -> frozenset[str]:
        """Bases reservadas fijas más las de DATABASE_DENYLIST."""
        return FORBIDDEN_DATABASE_NAMES | parse_denylist(self.database_denylist)

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _validate_database_url(cls, value: str | None) -> str | None:
        """Exige PostgreSQL con Psycopg 3 y bloquea bases reservadas."""
        if value is None:
            return None
        try:
            url = make_url(value)
        except ArgumentError as exc:
            raise ValueError("La URL de base de datos no es válida.") from exc

        if url.get_backend_name() != "postgresql" or url.get_driver_name() != "psycopg":
            raise ValueError(
                "La URL de base de datos debe usar PostgreSQL con Psycopg 3."
            )
        if not url.database:
            raise ValueError("La URL de base de datos debe incluir un nombre de base.")
        if url.database in FORBIDDEN_DATABASE_NAMES:
            raise ValueError(
                "La base de datos indicada está reservada y no puede utilizarse."
            )
        return value

    @model_validator(mode="after")
    def _validate_denylist(self) -> "Settings":
        """Rechaza las bases que el entorno local declara en DATABASE_DENYLIST."""
        denied = parse_denylist(self.database_denylist)
        for value in (self.database_url, self.test_database_url):
            if value is not None and make_url(value).database in denied:
                raise ValueError(
                    "La base de datos indicada está reservada y no puede utilizarse."
                )
        return self

    @model_validator(mode="after")
    def _validate_test_database(self) -> "Settings":
        """La base de pruebas debe ser nexora_test y no coincidir con desarrollo."""
        if self.test_database_url is None:
            return self

        test_url = make_url(self.test_database_url)
        development_url = make_url(self.database_url)

        if test_url.database != TEST_DATABASE_NAME:
            raise ValueError(
                f"TEST_DATABASE_URL debe apuntar exactamente a '{TEST_DATABASE_NAME}'."
            )
        if (
            self.test_database_url == self.database_url
            or test_url.database == development_url.database
        ):
            raise ValueError(
                "TEST_DATABASE_URL debe ser distinta de DATABASE_URL."
            )
        return self


settings = Settings()
