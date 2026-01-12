"""
TechTrainingPro - Configuration Module
Handles environment variables and app settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Settings
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_name: str = "TechTrainingPro"
    app_version: str = "2.0.0"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    
    # Google Gemini API
    gemini_api_key: Optional[str] = None
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_default_region: str = "ap-south-1"
    
    # Google Cloud Vision API
    google_vision_api_key: Optional[str] = None
    
    # Email Service
    resend_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
