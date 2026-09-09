import pytest

from app.config import get_settings


@pytest.fixture
def variables_de_entorno(tmp_path, monkeypatch):
    """Valores DUMMY -- nunca credenciales reales de Supabase. Ningún test de este paquete pega
    contra la red: sync.py/personas.py reciben un cliente httpx mockeado explícito donde hace
    falta."""
    monkeypatch.setenv("SUPABASE_URL", "https://dummy.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secreto-de-pruebas")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-de-pruebas")
    monkeypatch.setenv("DISPOSITIVO_ID", "checador-test")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "checador_test.db"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
