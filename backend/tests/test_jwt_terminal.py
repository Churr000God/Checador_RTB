import jwt
import pytest

from app.jwt_terminal import ROL, firmar_token


def test_firmar_token_incluye_el_rol_terminal_checador():
    token = firmar_token("secreto-de-pruebas")
    payload = jwt.decode(token, "secreto-de-pruebas", algorithms=["HS256"])
    assert payload["role"] == ROL == "terminal_checador"


def test_firmar_token_tiene_expiracion_futura():
    token = firmar_token("secreto-de-pruebas")
    payload = jwt.decode(token, "secreto-de-pruebas", algorithms=["HS256"])
    assert payload["exp"] > payload["iat"]


def test_firmar_token_falla_con_secreto_incorrecto():
    """El servidor (PostgREST) rechazaría este token -- mismo mecanismo de verificación."""
    token = firmar_token("secreto-correcto")
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "secreto-incorrecto", algorithms=["HS256"])
