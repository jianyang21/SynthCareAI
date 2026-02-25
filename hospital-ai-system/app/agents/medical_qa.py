"""Medical QA Agent — Answers patient health questions using RAG."""
from crewai import Agent
from app.core.llm_provider import get_llm
from app.tools.rag_search import search_patient_records
from app.tools.db_query import get_patient_info, get_patient_prescriptions


def create_medical_qa_agent() -> Agent:
    return Agent(
        role="Medical Information Specialist",
        goal=(
            "Answer the patient's health-related questions accurately using their "
            "medical records and EHR documents. Provide clear, empathetic, and "
            "professional medical information."
        ),
        backstory=(
            "You are a highly trained medical information specialist with access to "
            "the patient's complete electronic health records. You provide accurate, "
            "evidence-based answers grounded in the patient's medical history. "
            "You never fabricate medical information and always recommend consulting "
            "a doctor for serious concerns."
        ),
        tools=[search_patient_records, get_patient_info, get_patient_prescriptions],
        llm=get_llm(temperature=0.3),
        verbose=True,
        allow_delegation=False,
    )
