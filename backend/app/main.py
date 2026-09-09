"""App FastAPI del checador -- versión básica. Monta los 3 routers de UI (Marcar/Historial/
Config) + el placeholder de personas (sin UI, ver routers/personas.py) + estáticos (carpeta
vacía por ahora, la llena la sesión de frontend). Las plantillas Jinja2 son HTML plano SIN
estilos a propósito -- la identidad visual se aplica después, en otra pasada."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import conectar, inicializar_esquema, sembrar_personas_de_prueba
from app.routers import config as router_config
from app.routers import historial, marcar, personas

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conexion = conectar(get_settings().db_path)
    try:
        inicializar_esquema(conexion)
        sembrar_personas_de_prueba(conexion)
    finally:
        conexion.close()
    yield


app = FastAPI(title="Checador físico -- versión básica", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(marcar.router)
app.include_router(historial.router)
app.include_router(router_config.router)
app.include_router(personas.router)


@app.get("/")
def raiz() -> RedirectResponse:
    return RedirectResponse(url="/marcar")
