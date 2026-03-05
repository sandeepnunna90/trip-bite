from supabase import create_client, Client
from backend.config import get_settings

_anon_client: Client | None = None
_service_client: Client | None = None


def get_anon_client() -> Client:
    global _anon_client
    if _anon_client is None:
        s = get_settings()
        _anon_client = create_client(s.supabase_url, s.supabase_anon_key)
    return _anon_client


def get_service_client() -> Client:
    global _service_client
    if _service_client is None:
        s = get_settings()
        _service_client = create_client(s.supabase_url, s.supabase_service_role_key)
    return _service_client
