"""
Centralized LLM provider with automatic fallback.

Priority: Ollama (Granite4) → Gemini (Google AI)

Uses CrewAI's native LLM format for proper integration.
"""
import httpx
from crewai import LLM
from app.config.settings import settings
from app.core.logger import logger


def _is_ollama_running() -> bool:
    """Check if Ollama server is reachable."""
    try:
        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


def get_llm(temperature: float = 0.3):
    """
    Get the best available LLM using CrewAI's native LLM class.

    Tries Ollama first (local, free, private).
    Falls back to Gemini if Ollama is not running.
    """
    if _is_ollama_running():
        logger.info("llm_provider", provider="ollama", model=settings.OLLAMA_MODEL)
        return LLM(
            model=f"ollama/{settings.OLLAMA_MODEL}",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
        )

    if settings.GEMINI_API_KEY:
        logger.info("llm_provider", provider="gemini", model="gemini-1.5-flash")
        return LLM(
            model="gemini/gemini-1.5-flash",
            api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )

    raise RuntimeError(
        "No LLM available. Start Ollama (`ollama serve`) or set GEMINI_API_KEY in .env"
    )
