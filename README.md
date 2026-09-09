# Checador físico

Software del terminal de registro de marcas (checador) para el Sistema de Control de Jornada
(SCJ) de Distribuidora Central. **Repositorio propio, independiente de `sistema-control-jornada`**
— así lo especifica `SCJ-PRO-11 §V` de ese proyecto: "el checador es su propio subproyecto, con
su propio repositorio".

Esta es la **versión más básica posible**: sin Raspberry Pi todavía, sin lector biométrico
decidido. El objetivo es tener algo corriendo para empezar a probar el flujo completo
(marcar → guardar local → sincronizar contra el servidor real) con datos de prueba, dejando el
diseño a fondo (protocolo de lotes, reintentos, lector real) para después.

## Qué es y qué no es

- Contrato de datos de la marca (protocolo completo): `sistema-control-jornada/docs/00-contexto/SCJ-CDT-01_Contrato_de_Datos_de_la_Marca_V2_0.md`
- Lado servidor: `sistema-control-jornada/docs/07-procesos/SCJ-PRO-11_Proceso_Registro_por_Terminal_V1_0.md`
- Rol de Postgres de este terminal (ya existe en la base real, sólo INSERT en `tiempo.marca`):
  `sistema-control-jornada/db/ddl/37_tiempo_rls_terminal.sql`

Esta versión implementa un subconjunto deliberadamente chico de ese contrato -- ver
"Qué falta para la Raspberry Pi" abajo para todo lo que falta.

## Estructura

```
checador-fisico/
  backend/
    app/
      main.py          # FastAPI, monta routers + estáticos + templates
      config.py         # lee .env
      db.py              # SQLite plano (sin ORM), esquema + seed de personas de prueba
      schema.sql          # DDL local: marca, persona_cache
      lector.py            # abstracción del lector biométrico -- LectorStub, sin hardware real
      jwt_terminal.py       # autofirma el JWT (rol terminal_checador)
      sync.py                 # sube marcas pendientes a tiempo.marca del servidor real
      routers/
        marcar.py             # pestaña "Marcar"
        historial.py          # pestaña "Historial"
        config.py              # pestaña "Config" (dispositivo_id, pendientes, sincronizar ahora)
        personas.py             # placeholder de refresco de persona_cache -- ver docstring, TEMPORAL
      templates/                # HTML plano, SIN ESTILOS a propósito (ver abajo)
      static/                    # vacía -- la llena la sesión de frontend
    tests/                        # todo mockeado, nunca contra Supabase real
    pyproject.toml
    .env.example
  README.md
```

## Cómo correrlo

```bash
cd backend
cp .env.example .env   # llenar SUPABASE_URL / SUPABASE_JWT_SECRET / SUPABASE_SERVICE_ROLE_KEY /
                         # DISPOSITIVO_ID con los valores reales del proyecto de sistema-control-jornada
uv sync
uv run uvicorn app.main:app --reload
```

Abre `http://localhost:8000/marcar`. Al arrancar se crea `checador.db` (SQLite, ruta configurable
por `DB_PATH`) con el esquema y 2-3 personas de prueba precargadas (`app/db.py::sembrar_personas_de_prueba`,
`persona_id` claramente ficticios, prefijo `test-`).

Tests (todo mockeado, nunca pega contra Supabase real):

```bash
cd backend
uv run pytest
```

## Identidad visual

Las 4 plantillas de `app/templates/` (`base.html`, `marcar.html`, `historial.html`, `config.html`)
ya tienen la identidad visual de Kairos aplicada (`app/static/estilos.css` — paleta/tipografía de
`sistema-control-jornada/frontend/src/styles/tokens.css`), pensada para pantalla táctil de kiosco
(botones grandes, feedback inmediato al tocar, sin dependencia de hover/mouse).

## Qué falta para la Raspberry Pi

Explícitamente diferido en esta versión básica:

- **Lector biométrico real** -- `app/lector.py::LectorBiometrico` fija la interfaz
  (`leer_huella() -> plantilla_id`); falta el SDK según el hardware que se decida y una subclase
  que lo implemente. Hoy `LectorStub` no lee nada -- la UI simula la lectura dejando elegir una
  persona de una lista.
- **Protocolo de lote** -- `POST /marcas/lote`, tope 200, confirmación individual por marca. Hoy
  `sync.py` sube una por una, en un solo intento.
- **Reintento con espera creciente** -- 5s / 15s / 1min / 5min, tope 15min. Hoy `sync.py` es un
  intento simple: lo que falla queda pendiente para la próxima vez que alguien apriete
  "Sincronizar ahora" en `/config` (no hay job periódico todavía).
- **3 estados de reloj** (`sincronizado` / `deriva` / `sin_sincronizar`) -- hoy sólo hay un
  booleano (`reloj_sincronizado`), sin detección real de deriva.
- **Ventana de supresión de 60s** (evitar doble marca por doble lectura del mismo dedo).
- **Flujo B (bitácora de Operación)** -- fuera de alcance todavía, sólo se implementó el Flujo A
  (marca).
- **Caché de plantillas versionada por sello, refresco cada 15 min** -- hoy `persona_cache` se
  puebla a mano (seed de 2-3 personas de prueba) y `app/routers/personas.py` es sólo un
  placeholder de lectura bajo demanda.
- **Mecanismo de lectura de `personas.persona` más angosto que `service_role`** --
  `app/routers/personas.py` usa la `service_role` key del proyecto real como solución TEMPORAL de
  desarrollo/pruebas (bypasea RLS por completo). El rol real de este terminal
  (`terminal_checador`) no tiene SELECT en nada -- por diseño, un checador de pared comprometido
  no debe poder leer identidades. Antes de producción real hace falta diseñar algo más angosto
  (probablemente un endpoint de sólo lectura expuesto por el backend humano de
  `sistema-control-jornada`, no el terminal hablando directo con Supabase). **No usar esta ruta
  en producción tal cual está.**
