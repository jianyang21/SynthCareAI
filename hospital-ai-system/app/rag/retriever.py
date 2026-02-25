"""RAG retriever: Qdrant (primary) with PostgreSQL fallback."""
from typing import Optional

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config.settings import settings
from app.rag.embeddings import get_embeddings
from app.rag.qdrant_client import client as qdrant
from app.core.logger import logger


def retrieve(
    query: str,
    patient_id: Optional[int] = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Search Qdrant for relevant chunks, filtered by patient_id.
    Falls back to PostgreSQL if Qdrant fails.

    Returns list of {"content": str, "metadata": dict, "score": float}.
    """
    embeddings = get_embeddings()
    query_vec = embeddings.embed_query(query)

    # --- Primary: Qdrant ---
    try:
        search_filter = None
        if patient_id is not None:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="patient_id",
                        match=MatchValue(value=patient_id),
                    )
                ]
            )

        results = qdrant.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vec,
            query_filter=search_filter,
            limit=top_k,
        ).points

        chunks = []
        for hit in results:
            payload = hit.payload or {}
            chunks.append({
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
                "score": hit.score if hasattr(hit, "score") else 0.0,
                "source": "qdrant",
            })

        logger.info("rag_retrieve_qdrant", patient_id=patient_id, results=len(chunks))
        return chunks

    except Exception as exc:
        logger.warning("qdrant_fallback", error=str(exc))
        return _retrieve_pg_fallback(query, patient_id, top_k)


def _retrieve_pg_fallback(
    query: str,
    patient_id: Optional[int],
    top_k: int,
) -> list[dict]:
    """Fallback: simple text search in PostgreSQL document_chunks."""
    from sqlalchemy import create_engine, text
    from app.config.settings import settings as s

    # Use sync engine for fallback (simpler)
    sync_url = s.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    sql = """
        SELECT content, metadata, chunk_index
        FROM document_chunks
        WHERE patient_id = :pid
        ORDER BY chunk_index
        LIMIT :topk
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text(sql), {"pid": patient_id, "topk": top_k}
        ).fetchall()

    chunks = [
        {
            "content": row[0],
            "metadata": row[1] or {},
            "score": 0.0,
            "source": "postgresql",
        }
        for row in rows
    ]
    logger.info("rag_retrieve_pg_fallback", patient_id=patient_id, results=len(chunks))
    return chunks


def get_context_text(query: str, patient_id: Optional[int] = None, top_k: int = 5) -> str:
    """
    Convenience: retrieve chunks and return as a single context string.
    """
    chunks = retrieve(query, patient_id=patient_id, top_k=top_k)
    return "\n\n".join(c["content"] for c in chunks)
