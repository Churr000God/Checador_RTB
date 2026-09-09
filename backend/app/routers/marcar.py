"""Router de la pestaña "Marcar" -- versión básica. Sin lector real conectado todavía
(`app/lector.py::LectorStub`), así que la UI simula la lectura dejando elegir una persona de una
lista de `persona_cache` en vez de leer un dedo. `reloj_sincronizado` se fija en 1 (verdadero) --
esta versión no detecta deriva real del reloj del aparato todavía, ver README."""

import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request

from app.config import get_settings
from app.db import obtener_conexion
from app.templating import templates

router = APIRouter()


def _personas_disponibles(conexion: sqlite3.Connection) -> list[sqlite3.Row]:
    return conexion.execute(
        "SELECT plantilla_id, persona_id FROM persona_cache ORDER BY plantilla_id"
    ).fetchall()


@router.get("/marcar")
def formulario_marcar(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    return templates.TemplateResponse(
        request,
        "marcar.html",
        {"personas": _personas_disponibles(conexion), "marca_creada": None, "error": None},
    )


@router.post("/marcar")
def registrar_marca(
    request: Request,
    plantilla_id: int = Form(...),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    fila_persona = conexion.execute(
        "SELECT persona_id FROM persona_cache WHERE plantilla_id = ?", (plantilla_id,)
    ).fetchone()
    if fila_persona is None:
        return templates.TemplateResponse(
            request,
            "marcar.html",
            {
                "personas": _personas_disponibles(conexion),
                "marca_creada": None,
                "error": "Esa persona no está en la caché local (persona_cache).",
            },
            status_code=422,
        )

    evento_id = str(uuid.uuid4())
    hora_dispositivo = datetime.now(timezone.utc).isoformat()
    dispositivo_id = get_settings().dispositivo_id

    conexion.execute(
        "INSERT INTO marca "
        "(evento_id, dispositivo_id, persona_id, hora_dispositivo, reloj_sincronizado, sincronizado) "
        "VALUES (?, ?, ?, ?, 1, 0)",
        (evento_id, dispositivo_id, fila_persona["persona_id"], hora_dispositivo),
    )
    conexion.commit()

    return templates.TemplateResponse(
        request,
        "marcar.html",
        {
            "personas": _personas_disponibles(conexion),
            "marca_creada": {"evento_id": evento_id, "hora_dispositivo": hora_dispositivo},
            "error": None,
        },
    )
