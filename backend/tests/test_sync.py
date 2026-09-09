"""Tests de sync.py -- TODO MOCKEADO (httpx.MockTransport). Ningún test de este archivo pega
contra la red ni contra Supabase real."""

import json
import sqlite3

import httpx

from app.db import inicializar_esquema, sembrar_personas_de_prueba
from app.sync import DESFASE_LOCAL_CDMX, ORIGEN, sincronizar

PERSONA_DE_PRUEBA = "test-persona-0000-0000-0000-000000000001"


def _conexion(tmp_path) -> sqlite3.Connection:
    conexion = sqlite3.connect(str(tmp_path / "x.db"))
    conexion.row_factory = sqlite3.Row
    inicializar_esquema(conexion)
    sembrar_personas_de_prueba(conexion)
    return conexion


def _insertar_marca_pendiente(conexion, evento_id, reloj_sincronizado=1):
    conexion.execute(
        "INSERT INTO marca "
        "(evento_id, dispositivo_id, persona_id, hora_dispositivo, reloj_sincronizado, sincronizado) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        (evento_id, "disp-1", PERSONA_DE_PRUEBA, "2026-09-09T08:00:00+00:00", reloj_sincronizado),
    )
    conexion.commit()


def _cliente_mock(responder):
    return httpx.Client(transport=httpx.MockTransport(responder))


def test_sincronizar_marca_como_sincronizada_en_exito(tmp_path):
    conexion = _conexion(tmp_path)
    _insertar_marca_pendiente(conexion, "evt-1")
    payloads = []

    def responder(request: httpx.Request) -> httpx.Response:
        payloads.append(json.loads(request.content))
        return httpx.Response(201)

    resultado = sincronizar(
        conexion, "https://dummy.supabase.co", "secreto", "0.1.0-test", cliente_http=_cliente_mock(responder)
    )

    assert resultado.enviadas == 1
    assert resultado.fallidas == 0
    fila = conexion.execute(
        "SELECT sincronizado, hora_llegada_servidor FROM marca WHERE evento_id = 'evt-1'"
    ).fetchone()
    assert fila["sincronizado"] == 1
    assert fila["hora_llegada_servidor"] is not None

    payload = payloads[0]
    assert payload["evento_id"] == "evt-1"
    assert payload["persona_id"] == PERSONA_DE_PRUEBA
    assert payload["terminal_id"] == "disp-1"
    assert payload["secuencia_local"] == 1
    assert payload["momento_dispositivo"] == "2026-09-09T08:00:00+00:00"
    assert payload["desfase_local"] == DESFASE_LOCAL_CDMX == "-06:00"
    assert payload["origen"] == ORIGEN == "terminal"
    assert payload["estado_reloj"] == "sincronizado"
    assert payload["requiere_revision"] is False
    conexion.close()


def test_sincronizar_estado_reloj_sin_sincronizar_cuando_reloj_no_sincronizado(tmp_path):
    conexion = _conexion(tmp_path)
    _insertar_marca_pendiente(conexion, "evt-2", reloj_sincronizado=0)
    payloads = []

    def responder(request: httpx.Request) -> httpx.Response:
        payloads.append(json.loads(request.content))
        return httpx.Response(201)

    sincronizar(
        conexion, "https://dummy.supabase.co", "secreto", "0.1.0-test", cliente_http=_cliente_mock(responder)
    )

    assert payloads[0]["estado_reloj"] == "sin_sincronizar"
    conexion.close()


def test_sincronizar_no_marca_sincronizada_si_el_servidor_falla(tmp_path):
    conexion = _conexion(tmp_path)
    _insertar_marca_pendiente(conexion, "evt-3")

    def responder(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    resultado = sincronizar(
        conexion, "https://dummy.supabase.co", "secreto", "0.1.0-test", cliente_http=_cliente_mock(responder)
    )

    assert resultado.enviadas == 0
    assert resultado.fallidas == 1
    assert "evt-3" in resultado.errores[0]
    fila = conexion.execute("SELECT sincronizado FROM marca WHERE evento_id = 'evt-3'").fetchone()
    assert fila["sincronizado"] == 0
    conexion.close()


def test_sincronizar_una_marca_fallida_no_bloquea_las_demas(tmp_path):
    conexion = _conexion(tmp_path)
    _insertar_marca_pendiente(conexion, "evt-falla")
    _insertar_marca_pendiente(conexion, "evt-ok")

    def responder(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if payload["evento_id"] == "evt-falla":
            return httpx.Response(500)
        return httpx.Response(201)

    resultado = sincronizar(
        conexion, "https://dummy.supabase.co", "secreto", "0.1.0-test", cliente_http=_cliente_mock(responder)
    )

    assert resultado.enviadas == 1
    assert resultado.fallidas == 1
    fila_ok = conexion.execute("SELECT sincronizado FROM marca WHERE evento_id = 'evt-ok'").fetchone()
    fila_falla = conexion.execute("SELECT sincronizado FROM marca WHERE evento_id = 'evt-falla'").fetchone()
    assert fila_ok["sincronizado"] == 1
    assert fila_falla["sincronizado"] == 0
    conexion.close()


def test_sincronizar_sin_pendientes_no_llama_a_la_red(tmp_path):
    conexion = _conexion(tmp_path)
    llamadas = {"veces": 0}

    def responder(request: httpx.Request) -> httpx.Response:
        llamadas["veces"] += 1
        return httpx.Response(201)

    resultado = sincronizar(
        conexion, "https://dummy.supabase.co", "secreto", "0.1.0-test", cliente_http=_cliente_mock(responder)
    )

    assert resultado.enviadas == 0
    assert resultado.fallidas == 0
    assert llamadas["veces"] == 0
    conexion.close()


def test_sincronizar_envia_authorization_bearer_con_el_jwt_autofirmado(tmp_path):
    conexion = _conexion(tmp_path)
    _insertar_marca_pendiente(conexion, "evt-jwt")
    encabezados_recibidos = {}

    def responder(request: httpx.Request) -> httpx.Response:
        encabezados_recibidos.update(request.headers)
        return httpx.Response(201)

    sincronizar(
        conexion, "https://dummy.supabase.co", "secreto", "0.1.0-test", cliente_http=_cliente_mock(responder)
    )

    assert encabezados_recibidos["authorization"].startswith("Bearer ")
    assert encabezados_recibidos["content-profile"] == "tiempo"
    conexion.close()
