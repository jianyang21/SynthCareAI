"""CrewAI Tool: Parse prescriptions to extract medicine details."""
from crewai.tools import tool
from app.rag.retriever import get_context_text


@tool("parse_prescription")
def parse_prescription(patient_id: int) -> str:
    """
    Parse the patient's latest prescription documents to extract
    medicine names, dosages, and quantities for ordering.

    Args:
        patient_id: The patient's database ID.

    Returns:
        Extracted prescription details in structured format.
    """
    context = get_context_text(
        query="prescription medicines dosage medication drugs",
        patient_id=patient_id,
        top_k=5,
    )

    if not context.strip():
        return "No prescription documents found for this patient."

    return (
        "Prescription information found in EHR:\n"
        f"{context}\n\n"
        "Please review the above and extract medicine names, dosages, and quantities."
    )
