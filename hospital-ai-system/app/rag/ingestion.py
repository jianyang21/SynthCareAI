"""EHR document ingestion: PDF → chunks → Qdrant + PostgreSQL fallback."""
import uuid
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct, VectorParams, Distance

from app.config.settings import settings
from app.rag.embeddings import get_embeddings
from app.rag.qdrant_client import client as qdrant
from app.core.logger import logger


def _ensure_qdrant_collection(vector_size: int = 384):
    """Create the Qdrant collection if it doesn't already exist."""
    collections = [c.name for c in qdrant.get_collections().collections]
    if settings.QDRANT_COLLECTION not in collections:
        qdrant.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("qdrant_collection_created", name=settings.QDRANT_COLLECTION)


def ingest_pdf(
    file_path: str,
    patient_id: int,
    filename: str,
    db_session=None,
) -> dict:
    """
    Ingest a single PDF into Qdrant (with patient_id payload) and
    optionally store chunks in PostgreSQL as fallback.

    Returns: {"chunk_count": int, "point_ids": list[str]}
    """
    embeddings = get_embeddings()

    # 1. Load PDF
    logger.info("ingestion_started", patient_id=patient_id, file=filename)
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    all_chunks = text_splitter.split_documents(documents)

    if not all_chunks:
        logger.warning("no_chunks_extracted", file=filename)
        return {"chunk_count": 0, "point_ids": []}

    # 3. Embed
    texts = [c.page_content for c in all_chunks]
    vectors = embeddings.embed_documents(texts)

    # 4. Ensure collection exists
    _ensure_qdrant_collection(vector_size=len(vectors[0]) if vectors else 384)

    # 5. Upsert into Qdrant with patient_id in payload
    point_ids = []
    points = []
    for i, (text, vec) in enumerate(zip(texts, vectors)):
        pid = str(uuid.uuid4())
        point_ids.append(pid)
        points.append(
            PointStruct(
                id=pid,
                vector=vec,
                payload={
                    "patient_id": patient_id,
                    "content": text,
                    "chunk_index": i,
                    "filename": filename,
                },
            )
        )

    if points:
        qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points,
        )

    logger.info(
        "ingestion_complete",
        patient_id=patient_id,
        chunk_count=len(points),
    )

    # 6. PostgreSQL fallback (if session provided)
    if db_session is not None:
        _store_chunks_pg(db_session, patient_id, filename, all_chunks, point_ids)

    return {"chunk_count": len(points), "point_ids": point_ids}


def _store_chunks_pg(session, patient_id, filename, chunks, point_ids):
    """Store chunks in PostgreSQL as RAG fallback."""
    from app.db.models import EHRDocument, DocumentChunk

    ehr_doc = EHRDocument(
        patient_id=patient_id,
        filename=filename,
        chunk_count=len(chunks),
    )
    session.add(ehr_doc)
    session.flush()

    for i, (chunk, pid) in enumerate(zip(chunks, point_ids)):
        db_chunk = DocumentChunk(
            document_id=ehr_doc.id,
            patient_id=patient_id,
            content=chunk.page_content,
            chunk_index=i,
            metadata_=chunk.metadata if chunk.metadata else None,
            qdrant_point_id=pid,
        )
        session.add(db_chunk)

    session.commit()
    logger.info("pg_fallback_stored", patient_id=patient_id, chunks=len(chunks))
