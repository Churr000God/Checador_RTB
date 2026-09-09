"""Abstracción del lector biométrico -- versión básica, SIN hardware conectado todavía (el
usuario no decidió Raspberry Pi ni módulo lector). `routers/marcar.py` no llama a `leer_huella()`
en esta fase: la UI simula la lectura dejando elegir una persona de una lista de
`persona_cache` en vez de leer un dedo real.

Esta clase fija la INTERFAZ que el lector real va a implementar cuando se decida el hardware --
en ese momento se agrega una subclase nueva de `LectorBiometrico` y se cambia una sola línea en
el router. Ver README "Qué falta para la Raspberry Pi"."""

from abc import ABC, abstractmethod


class LecturaFallida(Exception):
    """Dedo no enrolado, timeout del módulo, módulo sin respuesta -- en el contrato real esto
    generaría un evento de Flujo B (bitácora), fuera de alcance de esta versión básica."""


class LectorBiometrico(ABC):
    @abstractmethod
    def leer_huella(self) -> int:
        """Devuelve el `plantilla_id` de la huella leída, o lanza `LecturaFallida`."""


class LectorStub(LectorBiometrico):
    """No lee nada real. Existe sólo para fijar la interfaz -- si algo llega a invocarlo por
    error, falla explícito en vez de simular una lectura falsa."""

    def leer_huella(self) -> int:
        raise LecturaFallida(
            "LectorStub no tiene hardware real conectado -- elegí la persona de la lista en /marcar."
        )
