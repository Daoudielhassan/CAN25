"""
Configuration management for AFCON Chatbot
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Groq Configuration
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Gemini Configuration (kept for backward compatibility)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    # OpenAI Configuration (kept for backward compatibility)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    
    embedding_model: str = "models/embedding-001"
    
    # ESPN API Configuration
    espn_base_url: str = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/caf.nations"
    refresh_interval: int = 30
    
    # Database Configuration
    database_url: str = "sqlite:///./data/afcon.db"
    
    # Vector Store Configuration
    vector_store_path: str = "./data/vector_store"
    vector_store_type: str = "faiss"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()