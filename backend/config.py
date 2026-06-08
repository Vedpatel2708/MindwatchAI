"""
backend/config.py — MINDWATCH
Loads environment variables from .env using Pydantic BaseSettings.
All other modules import `settings` from here — single source of truth.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Groq API — free LLM inference (Llama 3, 300-800 tok/sec)
    GROQ_API_KEY: str = Field(..., description="Groq API key from console.groq.com")

    # Supabase — free managed Postgres
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anon public key")

    # Crisis scoring threshold — assessments above this score get a risk alert
    CRISIS_THRESHOLD: float = Field(default=0.50, ge=0.0, le=1.0)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
