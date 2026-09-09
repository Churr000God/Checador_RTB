-- schema.sql -- esquema local del checador (SQLite, sin ORM). Se ejecuta con CREATE TABLE IF
-- NOT EXISTS al arrancar (app/db.py), nunca hay migraciones -- versión básica, sin Alembic ni
-- equivalente todavía.

CREATE TABLE IF NOT EXISTS persona_cache (
  plantilla_id  INTEGER PRIMARY KEY,
  persona_id    TEXT NOT NULL UNIQUE  -- FK conceptual a tiempo.persona.id del servidor (Supabase)
);

CREATE TABLE IF NOT EXISTS marca (
  numero_secuencial     INTEGER PRIMARY KEY AUTOINCREMENT,
  evento_id             TEXT NOT NULL UNIQUE,  -- UUID v4, generado al crear la marca localmente
  dispositivo_id        TEXT NOT NULL,
  persona_id            TEXT NOT NULL REFERENCES persona_cache (persona_id),
  hora_dispositivo      TEXT NOT NULL,   -- timestamp ISO, hora del reloj del aparato
  hora_llegada_servidor TEXT,            -- [CALCULADO] se llena al sincronizar OK, nullable
  reloj_sincronizado    INTEGER NOT NULL,  -- boolean 0/1
  sincronizado          INTEGER NOT NULL DEFAULT 0  -- boolean 0/1
);
