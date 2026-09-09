"""Placeholder de refresco de `persona_cache` -- sin pantalla propia, sin pestaña en el nav
(sólo Marcar/Historial/Config son pestañas de UI en esta versión básica).

Por qué es TEMPORAL: el rol de Postgres real que usará este terminal para escribir marcas
(`terminal_checador`, `sistema-control-jornada/db/ddl/37_tiempo_rls_terminal.sql`) sólo tiene
INSERT en `tiempo.marca` -- ni SELECT, ni en `personas.persona` ni en nada más, por diseño (un
checador de pared comprometido no debe poder leer identidades). Este endpoint, en cambio, usa la
SERVICE_ROLE KEY del proyecto Supabase real (bypasea RLS por completo) sólo para esta fase de
desarrollo/pruebas -- NUNCA debe llegar a producción así. El mecanismo real (probablemente un
endpoint de sólo lectura más angosto, expuesto por el backend humano de sistema-control-jornada
en vez de que el terminal hable directo con Supabase) queda pendiente de diseño -- ver README
"Qué falta para la Raspberry Pi".

Por eso este router sólo LEE personas.persona y las devuelve como JSON -- no escribe
`persona_cache`. Asignar `plantilla_id` sigue siendo manual por ahora, vía
`app/db.py::sembrar_personas_de_prueba` (2-3 personas de prueba fijas)."""

import httpx
from fastapi import APIRouter, HTTPException

from app.config import get_settings

router = APIRouter()


def listar_personas_activas(supabase_url: str, service_role_key: str) -> list[dict]:
    """GET personas.persona vía PostgREST directo con la service_role key -- ver docstring del
    módulo. Nunca se invoca contra Supabase real en tests, sólo con un cliente mockeado."""
    respuesta = httpx.get(
        f"{supabase_url.rstrip('/')}/rest/v1/persona",
        params={"select": "id,primer_nombre,apellido_paterno", "estado": "eq.activo"},
        headers={
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
            "Accept-Profile": "personas",
        },
        timeout=10.0,
    )
    respuesta.raise_for_status()
    return respuesta.json()


@router.get("/personas/activas")
def personas_activas() -> list[dict]:
    settings = get_settings()
    try:
        return listar_personas_activas(settings.supabase_url, settings.supabase_service_role_key)
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502, detail=f"No se pudo leer personas.persona: {error}"
        ) from error
