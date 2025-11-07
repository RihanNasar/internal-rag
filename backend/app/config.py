from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database - Handle Render's postgres:// URL format
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/internal_rag")
    
    @property
    def sqlalchemy_database_url(self) -> str:
        """Convert postgres:// to postgresql:// for SQLAlchemy"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Email - Using Brevo (formerly Sendinblue) HTTP API
    brevo_api_key: str = os.getenv("BREVO_API_KEY", "")
    email_from_name: str = os.getenv("EMAIL_FROM_NAME", "Task Assignment AI")
    email_from_address: str = os.getenv("EMAIL_FROM_ADDRESS", "mrnzero321@gmail.com")
    
    # Frontend
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # AI Settings
    confidence_threshold: float = 0.75
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "Task Assignment AI"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # ChromaDB
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
