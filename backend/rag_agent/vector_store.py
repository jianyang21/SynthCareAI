from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance,
    Filter, FieldCondition, MatchValue,
    PointStruct,
)
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import uuid
from datetime import datetime

# =========================
# CONFIG
# =========================

COLLECTION = "hybrid_medical_records"

embedder = SentenceTransformer("all-MiniLM-L6-v2")

qdrant = QdrantClient(path="qdrant_db")

if COLLECTION not in [c.name for c in qdrant.get_collections().collections]:
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )


# =========================
# HELPERS
# =========================

def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks


def _make_point(vector, payload) -> PointStruct:
    """Wrap vector + payload into a PointStruct (required by new qdrant-client)."""
    return PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload=payload,
    )


# =========================
# STORE PDF
# =========================

def store_pdf_hybrid(file, patient_id: int, record_type: str):
    reader = PdfReader(file)
    points = []

    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue

        chunks = chunk_text(page_text)
        chunk_vectors = embedder.encode(chunks).tolist()

        for i, chunk in enumerate(chunks):
            points.append(_make_point(
                vector=chunk_vectors[i],
                payload={
                    "patient_id": patient_id,
                    "record_type": record_type,
                    "text": chunk,
                    "page_number": page_num + 1,
                    "chunk_index": i,
                    "full_page_text": page_text,
                    "date": datetime.utcnow().isoformat(),
                }
            ))

    qdrant.upsert(collection_name=COLLECTION, points=points)
    return {"status": "stored", "total_chunks": len(points)}


# =========================
# STORE MANUAL TEXT
# =========================

def store_text_hybrid(text: str, patient_id: int, record_type="doctor_note"):
    chunks = chunk_text(text)
    vectors = embedder.encode(chunks).tolist()

    points = [
        _make_point(
            vector=vectors[i],
            payload={
                "patient_id": patient_id,
                "record_type": record_type,
                "text": chunk,
                "page_number": -1,
                "chunk_index": i,
                "full_page_text": text,
                "date": datetime.utcnow().isoformat(),
            }
        )
        for i, chunk in enumerate(chunks)
    ]

    qdrant.upsert(collection_name=COLLECTION, points=points)
    return {"status": "stored"}


# =========================
# SEARCH
# =========================

def search_hybrid(patient_id: int, query: str, limit: int = 5):
    query_vector = embedder.encode(query).tolist()

    # qdrant-client >= 1.7 — use query_points() instead of search()
    response = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=limit,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="patient_id",
                    match=MatchValue(value=patient_id),
                )
            ]
        ),
    )

    return [
        {
            "answer_chunk":      r.payload["text"],
            "page_number":       r.payload["page_number"],
            "record_type":       r.payload["record_type"],
            "full_page_preview": r.payload["full_page_text"][:500],
            "date":              r.payload["date"],
        }
        for r in response.points      # .points — QueryResponse wraps the list
    ]


# =========================
# ADD DOCTOR COMMENT
# =========================

def add_comment_hybrid(patient_id: int, comment: str):
    vector = embedder.encode(comment).tolist()

    qdrant.upsert(
        collection_name=COLLECTION,
        points=[
            _make_point(
                vector=vector,
                payload={
                    "patient_id": patient_id,
                    "record_type": "doctor_comment",
                    "text": comment,
                    "page_number": -1,
                    "chunk_index": 0,
                    "full_page_text": comment,
                    "date": datetime.utcnow().isoformat(),
                }
            )
        ],
    )
    return {"status": "comment added"}