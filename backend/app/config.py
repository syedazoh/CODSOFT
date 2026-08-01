"""Application Configuration"""
import os
from typing import Optional

class Settings:
    """Application settings from environment variables"""
    app_name: str = "Startup Simulator"
    app_version: str = "0.1.0"
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/startup_simulator")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

settings = Settings()