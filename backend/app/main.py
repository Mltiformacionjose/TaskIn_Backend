"""Punto de entrada de la API de Nexora.

En esta fase solo se crea la instancia de FastAPI. Los routers se
registrarán bajo el prefijo /api/v1 cuando se desarrollen los módulos.
"""

from fastapi import FastAPI

app = FastAPI(title="Nexora API", version="0.1.0")
