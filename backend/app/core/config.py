from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AlphaTrigger AI"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "alphatrigger"
    DATABASE_URL: Optional[str] = None

    # CORS: comma-separated list of allowed browser origins
    FRONTEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Market Data
    MARKET_DATA_PROVIDER: str = "mock" # mock or yfinance

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.FRONTEND_CORS_ORIGINS.split(",") if o.strip()]

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
