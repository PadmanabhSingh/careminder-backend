import os
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment variables

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def require_env(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value

def get_supabase_url() -> str:
    return require_env("SUPABASE_URL", SUPABASE_URL)

def get_supabase_service_key() -> str:
    return require_env("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY)