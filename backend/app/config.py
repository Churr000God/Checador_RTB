"""Configuración leída de variables de entorno (.env en backend/, ver .env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_jwt_secret: str
    # TEMPORAL -- sólo la usa app/routers/personas.py, ver docstring de ese módulo.
    supabase_service_role_key: str
    dispositivo_id: str
    db_path: str = "checador.db"
    version_software: str = "0.1.0-basico"


@lru_cache
def get_settings() -> Settings:
    return Settings()
