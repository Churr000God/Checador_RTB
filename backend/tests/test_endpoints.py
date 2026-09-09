"""Smoke tests de los endpoints de UI -- SQLite en un archivo temporal (tmp_path), preparado a
mano (sin depender del lifespan de FastAPI). Ningún test de este archivo pega contra Supabase --
`sync`/`personas` no se ejercitan acá, tienen sus propios tests mockeados.

Los asserts sobre el HTML apuntan a clases CSS (`contador-pendientes`, `insignia-kiosco--...`),
nunca a copy literal -- frontend puede reescribir el texto de las plantillas sin romper estos
tests, mismo criterio que ya rompió una vez el assert de "Marcas pendientes de sincronizar: 1"."""

import re

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import conectar, inicializar_esquema, sembrar_personas_de_prueba
from app.main import app

PERSONA_DE_PRUEBA = "test-persona-0000-0000-0000-000000000001"


def _preparar_db():
    settings = get_settings()
    conexion = conectar(settings.db_path)
    inicializar_esquema(conexion)
    sembrar_personas_de_prueba(conexion)
    conexion.close()


def test_marcar_get_lista_las_personas_de_prueba(variables_de_entorno):
    _preparar_db()
    client = TestClient(app)

    respuesta = client.get("/marcar")

    assert respuesta.status_code == 200
    assert PERSONA_DE_PRUEBA in respuesta.text


def test_marcar_post_crea_fila_local_y_aparece_en_historial(variables_de_entorno):
    _preparar_db()
    client = TestClient(app)

    respuesta = client.post("/marcar", data={"plantilla_id": 1})

    assert respuesta.status_code == 200
    assert "Marca registrada" in respuesta.text

    respuesta_historial = client.get("/historial")
    assert respuesta_historial.status_code == 200
    assert PERSONA_DE_PRUEBA in respuesta_historial.text
    # sincronizado=0 todavía -- nadie llamó a /config. Se ata a la clase CSS del badge, no al
    # texto ("Pendiente"/"Sincronizado") que frontend puede reescribir.
    assert "insignia-kiosco--pendiente" in respuesta_historial.text
    assert "insignia-kiosco--ok" not in respuesta_historial.text


def test_marcar_post_plantilla_inexistente_devuelve_422(variables_de_entorno):
    _preparar_db()
    client = TestClient(app)

    respuesta = client.post("/marcar", data={"plantilla_id": 999})

    assert respuesta.status_code == 422


def test_config_get_muestra_dispositivo_id_y_conteo_de_pendientes(variables_de_entorno):
    _preparar_db()
    client = TestClient(app)
    client.post("/marcar", data={"plantilla_id": 1})

    respuesta = client.get("/config")

    assert respuesta.status_code == 200
    assert "checador-test" in respuesta.text
    # Se ata a la clase CSS del contador (`contador-pendientes`), no a la copia exacta -- ese
    # texto ya cambió una vez con el rediseño de frontend y rompió un assert literal.
    coincidencia = re.search(r'class="contador-pendientes[^"]*">\s*(\d+)\s*<', respuesta.text)
    assert coincidencia is not None, "no se encontró el contador de pendientes en el HTML"
    assert coincidencia.group(1) == "1"
