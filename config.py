from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    groq_api_key: str = ""  # Added GROQ_API_KEY setting
    voyage_api_key: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
