from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")

    # --- LLM (Ollama primary, Gemini fallback) ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "granite4:micro-h")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # --- Qdrant ---
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "hospital_ehr")

    # --- Hospital ---
    HOSPITAL_TELEGRAM_ID: str = os.getenv("HOSPITAL_TELEGRAM_ID", "")
    ALLOWED_TELEGRAM_IDS: str = os.getenv("ALLOWED_TELEGRAM_IDS", "")  # comma-separated


settings = Settings()
