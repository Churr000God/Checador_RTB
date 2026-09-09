"""Router de la pestaña "Historial" -- últimas N marcas locales con su estado de
sincronización."""

import sqlite3

from fastapi import APIRouter, Depends, Query, Request

from app.db import obtener_conexion
from app.templating import templates

router = APIRouter()

LIMITE_DEFECTO = 50
LIMITE_MAXIMO = 500


@router.get("/historial")
def historial(
    request: Request,
    limite: int = Query(LIMITE_DEFECTO, ge=1, le=LIMITE_MAXIMO),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    marcas = conexion.execute(
        "SELECT * FROM marca ORDER BY numero_secuencial DESC LIMIT ?", (limite,)
    ).fetchall()
    return templates.TemplateResponse(request, "historial.html", {"marcas": marcas})
