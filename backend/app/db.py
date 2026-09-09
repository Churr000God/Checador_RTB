"""Acceso a la base local SQLite -- stdlib `sqlite3` plano, sin ORM (versión básica del
checador). Sin pool: cada request abre y cierra su propia conexión corta, suficiente para un solo
proceso/aparato a la escala de un kiosco."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from app.config import get_settings

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def conectar(db_path: str) -> sqlite3.Connection:
    conexion = sqlite3.connect(db_path)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_esquema(conexion: sqlite3.Connection) -> None:
    conexion.executescript(_SCHEMA_PATH.read_text())
    conexion.commit()


# persona_id claramente ficticios (prefijo "test-") -- NUNCA valores reales de personas.persona.
# Asignación manual de plantilla_id mientras no exista el mecanismo real de refresco (ver
# app/routers/personas.py) -- alcanza con 2-3 personas de prueba para poder probar /marcar.
PERSONAS_DE_PRUEBA = (
    (1, "test-persona-0000-0000-0000-000000000001"),
    (2, "test-persona-0000-0000-0000-000000000002"),
    (3, "test-persona-0000-0000-0000-000000000003"),
)


def sembrar_personas_de_prueba(conexion: sqlite3.Connection) -> None:
    """Idempotente (INSERT OR IGNORE) -- no pisa una caché ya poblada de verdad."""
    conexion.executemany(
        "INSERT OR IGNORE INTO persona_cache (plantilla_id, persona_id) VALUES (?, ?)",
        PERSONAS_DE_PRUEBA,
    )
    conexion.commit()


def obtener_conexion() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI -- una conexión por request, cerrada al final."""
    conexion = conectar(get_settings().db_path)
    try:
        yield conexion
    finally:
        conexion.close()
