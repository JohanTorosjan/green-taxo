from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://greentaxo:changeme@db:5432/greentaxo_db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Green-Taxo"
    OPENAI_API_KEY: Optional[str] = None
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()