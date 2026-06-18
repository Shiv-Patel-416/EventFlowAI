"""EventFlow AI — Configuration"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "EventFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database (Using SQLite for seamless local prototype execution)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./eventflow.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "eventflow-ai-secret-key-2024-flipkart-grid")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # ML Models
    MODELS_DIR: str = os.getenv("MODELS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "models"))
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "data"))
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000", "http://frontend:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
