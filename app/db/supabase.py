from supabase import create_client, Client
from app.core.config import get_supabase_url, get_supabase_service_key

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            get_supabase_url(),
            get_supabase_service_key()
        )
    return _supabase