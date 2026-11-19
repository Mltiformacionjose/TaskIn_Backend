# TaskIn — Backend

TaskIn es una aplicación web de gestión de tareas y listas personales y compartidas. Este repositorio contiene el **backend**: la API, la lógica de negocio y el acceso a datos. El frontend vive en otro repositorio y se comunica con este por HTTP; **nunca accede directamente a PostgreSQL**.

> **Estado real (2026-11-19):** solo hay infraestructura. Existen la aplicación FastAPI vacía, la configuración, la conexión a PostgreSQL, Alembic sin migraciones y pruebas de infraestructura. **No hay endpoints, modelos ni autenticación.** El modelo de datos v0.6 (7 tablas) es **definitivo** y está en `Nexora-Documentation/11-backend/database/`; se va a implementar paso a paso.
>
> El nombre del proyecto es TaskIn (ADR-0012). Las bases `nexora_dev` y `nexora_test` y el rol `nexora` conservan su nombre: son del entorno local.

## Responsabilidad

Exponer la API, validar entradas, aplicar reglas de negocio, autorizar y comunicarse con PostgreSQL. Ver ARCHITECTURE_BACKEND (`Nexora-Documentation/11-backend/ARCHITECTURE_BACKEND.md`).

## Tecnologías

Python, FastAPI 0.162.7, Uvicorn 0.54.0, SQLAlchemy 2.1.8, Psycopg 3.3.9, Alembic 1.20.1, pydantic-settings 2.16.3, pytest 9.2.0, pytest-bdd 9.0.1, httpx 0.28.1. Base de datos: **PostgreSQL 18**.

## Requisitos previos

- Python 3 reciente (el proyecto se ha usado con Python 3.14; la versión mínima no está documentada).
- PostgreSQL 18 en marcha con dos bases vacías: una de desarrollo y `nexora_test` para pruebas.
- Un rol de base de datos con permisos sobre ambas bases (sin privilegios de superusuario).

## Instalación (PowerShell, desde esta carpeta)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Variables de entorno

Copia `.env.example` a `.env` y sustituye los marcadores. **Nunca subas `.env` ni escribas credenciales reales en documentos.**

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | `postgresql+psycopg://USUARIO:CLAVE@host:puerto/base_de_desarrollo` |
| `TEST_DATABASE_URL` | Solo para pruebas de integración | Debe apuntar exactamente a la base `nexora_test` y ser distinta de `DATABASE_URL` |
| `FRONTEND_ORIGIN` | No (por defecto `http://localhost:3000`) | Origen del frontend; aún no se usa en CORS |
| `DATABASE_DENYLIST` | No | Otras bases de tu equipo que TaskIn nunca debe usar, separadas por comas (por ejemplo, las de otros proyectos). `postgres` siempre está bloqueada. Si una URL apunta a una de ellas, la aplicación no arranca |

Pendientes de decisión, aún sin definir: `SECRET_KEY`, correo electrónico, CORS/SameSite/CSRF.

## PostgreSQL

Versión principal: 18 (decisión ADR-0001). El proyecto **no crea el esquema** ni ejecuta migraciones; la configuración concreta de tu instalación (puerto, roles, rutas) es local y no se documenta aquí. Para comprobar la conexión:

```powershell
python -m app.db.check          # base de desarrollo (SELECT 1)
python -m app.db.check --test   # base de pruebas
```

## Arranque local

```powershell
python -m uvicorn app.main:app --reload
```

La aplicación arranca, pero **no expone rutas propias**. Por defecto FastAPI publica la documentación interactiva en `/docs` y `/openapi.json`; el contrato HTTP definitivo está pendiente (ver API_CONTRACT (`Nexora-Documentation/11-backend/API_CONTRACT.md`)).

## Pruebas

```powershell
python -m pytest                       # todas (integración requiere PostgreSQL)
python -m pytest -m "not integration"  # sin base de datos
```

Detalle en TESTING_BACKEND (`Nexora-Documentation/11-backend/TESTING_BACKEND.md`). Este README no afirma que las pruebas pasen.

## Migraciones

Alembic está configurado (toma la URL de `DATABASE_URL`) pero `alembic/versions/` aún está vacío. La primera migración se creará a partir del modelo definitivo (DATABASE_DESIGN, `Nexora-Documentation/11-backend/DATABASE_DESIGN.md`).

## Estructura del proyecto

```
app/        main.py, core/ (config, errores, seguridad), db/ (base, sesión, comprobaciones)
            models/ routers/ schemas/ services/ dependencies/  (vacíos, previstos)
alembic/    configuración de migraciones (sin versiones)
tests/      pruebas (unitarias, integración, Gherkin de infraestructura)
```

## Documentación

Este repositorio no contiene documentación (petición de la profesora; ADR-0002 v0.2). Toda la documentación del proyecto, incluida la técnica del backend, está en la carpeta independiente **Nexora-Documentation**: `11-backend/` (arquitectura, estructura, pruebas y demás) y el resto de carpetas (requisitos, flujos, dominio, diseño, decisiones).
