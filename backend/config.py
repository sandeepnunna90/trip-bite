from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_places_api_key: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    anthropic_api_key: str = ""
    apify_api_token: str = ""
    resend_api_key: str = ""
    resend_from_email: str = "hello@tripbite.app"
    backend_url: str = "http://localhost:8000"

    use_mock_google: bool = False
    use_mock_apify: bool = False
    use_mock_claude: bool = False
    use_mock_resend: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
