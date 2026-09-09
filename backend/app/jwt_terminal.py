"""Autofirma el JWT que autentica este terminal ante PostgREST (Supabase) -- mismo mecanismo que
usa Supabase internamente para los roles anon/authenticated/service_role (HS256 con el secreto
del proyecto), pero con un claim de rol PROPIO (`role=terminal_checador`) en vez de pasar por el
login de Supabase Auth: el terminal no es un usuario humano, no tiene sesión.

Ver `db/ddl/37_tiempo_rls_terminal.sql` en sistema-control-jornada -- ese rol de Postgres sólo
tiene INSERT en `tiempo.marca`, nada más, con `origen='terminal'` forzado por policy."""

import time

import jwt

ROL = "terminal_checador"
VIGENCIA_SEGUNDOS = 60 * 60  # 1h -- de sobra para un intento de sync; se refirma cada vez que se
# necesita, no se cachea entre requests (esta versión básica no tiene volumen que lo justifique).


def firmar_token(secreto: str) -> str:
    ahora = int(time.time())
    payload = {"role": ROL, "iat": ahora, "exp": ahora + VIGENCIA_SEGUNDOS}
    return jwt.encode(payload, secreto, algorithm="HS256")
