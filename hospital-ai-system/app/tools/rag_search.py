"""CrewAI Tool: Search patient medical records via RAG."""
from crewai.tools import tool
from app.rag.retriever import retrieve, get_context_text


@tool("search_patient_records")
def search_patient_records(query: str, patient_id: int) -> str:
    """
    Search the patient's medical records (EHR documents) for relevant information.
    Uses the RAG pipeline to find the most relevant medical context.

    Args:
        query: The medical question or search term.
        patient_id: The patient's database ID.

    Returns:
        Relevant medical context from the patient's EHR documents.
    """
    chunks = retrieve(query=query, patient_id=patient_id, top_k=5)
    if not chunks:
        return "No medical records found for this patient."

    result_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "unknown")
        result_parts.append(f"[Source {i} ({source})]\n{chunk['content']}")

    return "\n\n".join(result_parts)
