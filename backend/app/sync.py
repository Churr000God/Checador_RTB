"""Sincroniza marcas locales pendientes (`sincronizado = 0`) contra `tiempo.marca` del servidor
real (Supabase), vía PostgREST directo con el JWT autofirmado (`jwt_terminal.py`) como
Authorization Bearer.

Versión básica -- INTENTO SIMPLE, una sola pasada, sin protocolo de lote (tope 200) ni reintento
con espera creciente (5s/15s/1min/5min, tope 15min) todavía. Una marca que falla no aborta las
demás -- se sigue con la siguiente y se reporta el conteo al final. Ver README "Qué falta para
la Raspberry Pi".

Mapeo hacia `tiempo.marca` (columnas reales, `sistema-control-jornada/db/ddl/02_tiempo.sql`):
- numero_secuencial   -> secuencia_local
- dispositivo_id      -> terminal_id
- hora_dispositivo    -> momento_dispositivo
- reloj_sincronizado  -> estado_reloj ("sincronizado" si True, "sin_sincronizar" si False --
                         el 3er estado "deriva" se difiere, ver README)
- (fijo)              -> desfase_local = "-06:00" (CDMX, sin horario de verano)
- (fijo)              -> origen = "terminal"
- (fijo)              -> requiere_revision = false (el trigger del servidor lo recalcula después,
                         mismo patrón que ya usa captura_manual en sistema-control-jornada)
- evento_id, persona_id: tal cual."""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from app.jwt_terminal import firmar_token

DESFASE_LOCAL_CDMX = "-06:00"
ORIGEN = "terminal"


@dataclass
class ResultadoSync:
    enviadas: int
    fallidas: int
    errores: list[str] = field(default_factory=list)


def _fila_a_payload(fila: sqlite3.Row, version_software: str) -> dict:
    return {
        "evento_id": fila["evento_id"],
        "persona_id": fila["persona_id"],
        "terminal_id": fila["dispositivo_id"],
        "secuencia_local": fila["numero_secuencial"],
        "momento_dispositivo": fila["hora_dispositivo"],
        "desfase_local": DESFASE_LOCAL_CDMX,
        "estado_reloj": "sincronizado" if fila["reloj_sincronizado"] else "sin_sincronizar",
        "version_software": version_software,
        "origen": ORIGEN,
        "requiere_revision": False,
    }


def sincronizar(
    conexion: sqlite3.Connection,
    supabase_url: str,
    jwt_secret: str,
    version_software: str,
    cliente_http: httpx.Client | None = None,
) -> ResultadoSync:
    """`cliente_http` es inyectable a propósito -- en tests se pasa uno con `transport` mockeado
    (`httpx.MockTransport`), nunca se pega contra Supabase real desde el paquete de tests."""
    filas = conexion.execute(
        "SELECT * FROM marca WHERE sincronizado = 0 ORDER BY numero_secuencial"
    ).fetchall()
    if not filas:
        return ResultadoSync(enviadas=0, fallidas=0)

    token = firmar_token(jwt_secret)
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": token,
        "Content-Profile": "tiempo",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    url = f"{supabase_url.rstrip('/')}/rest/v1/marca"

    cerrar_cliente = cliente_http is None
    cliente = cliente_http or httpx.Client()
    enviadas = 0
    errores: list[str] = []
    try:
        for fila in filas:
            payload = _fila_a_payload(fila, version_software)
            try:
                respuesta = cliente.post(url, json=payload, headers=headers)
                respuesta.raise_for_status()
            except httpx.HTTPError as error:
                errores.append(f"{fila['evento_id']}: {error}")
                continue

            ahora_iso = datetime.now(timezone.utc).isoformat()
            conexion.execute(
                "UPDATE marca SET sincronizado = 1, hora_llegada_servidor = ? "
                "WHERE numero_secuencial = ?",
                (ahora_iso, fila["numero_secuencial"]),
            )
            enviadas += 1
        conexion.commit()
    finally:
        if cerrar_cliente:
            cliente.close()

    return ResultadoSync(enviadas=enviadas, fallidas=len(errores), errores=errores)
