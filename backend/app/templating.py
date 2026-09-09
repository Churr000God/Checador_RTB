"""Instancia única de Jinja2Templates, con ruta ABSOLUTA (no depende de desde dónde se invoque
`uvicorn`) -- compartida por todos los routers."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
