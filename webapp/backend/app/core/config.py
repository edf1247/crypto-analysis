from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: list[str] = ["http://localhost:5175","http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://[::1]:5173"]

    class Config:
        env_file = ".env"

settings = Settings()
