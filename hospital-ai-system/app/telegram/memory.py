"""Conversation memory: Redis (short-term) + PostgreSQL (long-term)."""
import json
from datetime import datetime
from typing import Optional

from app.core.redis_client import redis_client
from app.core.logger import logger

# Redis key prefix and max short-term messages
REDIS_PREFIX = "chat_memory:"
MAX_SHORT_TERM = 20  # keep last 20 messages in Redis


def _key(patient_id: int) -> str:
    return f"{REDIS_PREFIX}{patient_id}"


# ──────────────────────  Short-term (Redis)  ──────────────────────


def save_message_short(patient_id: int, role: str, content: str):
    """Save a message to Redis short-term memory."""
    msg = json.dumps({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    })
    key = _key(patient_id)
    redis_client.rpush(key, msg)
    redis_client.ltrim(key, -MAX_SHORT_TERM, -1)  # keep only last N


def get_recent_messages(patient_id: int, count: int = 10) -> list[dict]:
    """Get recent messages from Redis."""
    key = _key(patient_id)
    raw = redis_client.lrange(key, -count, -1)
    return [json.loads(m) for m in raw]


def get_chat_history_text(patient_id: int, count: int = 10) -> str:
    """Get recent chat history as formatted text for LLM context."""
    messages = get_recent_messages(patient_id, count)
    if not messages:
        return ""
    lines = []
    for msg in messages:
        role = "Patient" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def clear_memory(patient_id: int):
    """Clear short-term memory for a patient."""
    redis_client.delete(_key(patient_id))


# ──────────────────────  Long-term (PostgreSQL)  ──────────────────────


def save_message_long(patient_id: int, role: str, content: str):
    """Save a message to PostgreSQL long-term memory."""
    from sqlalchemy import create_engine, text
    from app.config.settings import settings

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO conversation_messages (patient_id, role, content) "
                "VALUES (:pid, :role, :content)"
            ),
            {"pid": patient_id, "role": role, "content": content},
        )
        conn.commit()


def save_message(patient_id: int, role: str, content: str):
    """Save to both short-term and long-term memory."""
    save_message_short(patient_id, role, content)
    try:
        save_message_long(patient_id, role, content)
    except Exception as exc:
        logger.warning("long_term_memory_save_failed", error=str(exc))
