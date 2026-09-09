"""Router de la pestaña "Config" -- dispositivo_id, contador de pendientes, y un botón para
forzar una sincronización ahora mismo. Versión básica: no hay job periódico todavía (sin
APScheduler ni equivalente) -- sync sólo corre cuando alguien lo pide desde acá. Ver README."""

import sqlite3

from fastapi import APIRouter, Depends, Request

from app.config import get_settings
from app.db import obtener_conexion
from app.sync import sincronizar
from app.templating import templates

router = APIRouter()


def _contar_pendientes(conexion: sqlite3.Connection) -> int:
    fila = conexion.execute("SELECT COUNT(*) AS total FROM marca WHERE sincronizado = 0").fetchone()
    return fila["total"]


@router.get("/config")
def formulario_config(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "config.html",
        {
            "dispositivo_id": settings.dispositivo_id,
            "pendientes": _contar_pendientes(conexion),
            "resultado_sync": None,
        },
    )


@router.post("/config")
def forzar_sincronizacion(request: Request, conexion: sqlite3.Connection = Depends(obtener_conexion)):
    settings = get_settings()
    resultado = sincronizar(
        conexion, settings.supabase_url, settings.supabase_jwt_secret, settings.version_software
    )
    return templates.TemplateResponse(
        request,
        "config.html",
        {
            "dispositivo_id": settings.dispositivo_id,
            "pendientes": _contar_pendientes(conexion),
            "resultado_sync": resultado,
        },
    )
