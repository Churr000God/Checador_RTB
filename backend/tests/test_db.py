from app.db import PERSONAS_DE_PRUEBA, conectar, inicializar_esquema, sembrar_personas_de_prueba


def test_inicializar_esquema_crea_las_2_tablas(tmp_path):
    conexion = conectar(str(tmp_path / "x.db"))
    inicializar_esquema(conexion)

    tablas = {
        fila[0]
        for fila in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"marca", "persona_cache"} <= tablas
    conexion.close()


def test_inicializar_esquema_es_idempotente(tmp_path):
    """CREATE TABLE IF NOT EXISTS -- correrlo 2 veces (arranque + tests) no debe romper nada."""
    conexion = conectar(str(tmp_path / "x.db"))
    inicializar_esquema(conexion)
    inicializar_esquema(conexion)
    conexion.close()


def test_sembrar_personas_de_prueba_inserta_las_fixtures(tmp_path):
    conexion = conectar(str(tmp_path / "x.db"))
    inicializar_esquema(conexion)
    sembrar_personas_de_prueba(conexion)

    filas = conexion.execute(
        "SELECT plantilla_id, persona_id FROM persona_cache ORDER BY plantilla_id"
    ).fetchall()
    assert [(fila["plantilla_id"], fila["persona_id"]) for fila in filas] == list(PERSONAS_DE_PRUEBA)
    conexion.close()


def test_sembrar_personas_de_prueba_es_idempotente_no_duplica(tmp_path):
    conexion = conectar(str(tmp_path / "x.db"))
    inicializar_esquema(conexion)
    sembrar_personas_de_prueba(conexion)
    sembrar_personas_de_prueba(conexion)

    total = conexion.execute("SELECT COUNT(*) AS total FROM persona_cache").fetchone()["total"]
    assert total == len(PERSONAS_DE_PRUEBA)
    conexion.close()
