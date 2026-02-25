"""Emergency Agent — Detects abnormalities and triggers Telegram alerts."""
from crewai import Agent
from app.core.llm_provider import get_llm
from app.tools.emergency_alert import trigger_emergency_alert
from app.tools.rag_search import search_patient_records
from app.tools.db_query import get_patient_info


def create_emergency_agent() -> Agent:
    return Agent(
        role="Emergency Detection Specialist",
        goal=(
            "Monitor patient conversations for signs of medical emergencies, "
            "abnormal symptoms, or distress. When an emergency is detected, "
            "immediately alert the hospital and the patient's emergency contacts via Telegram."
        ),
        backstory=(
            "You are an AI emergency detection specialist. You analyze patient "
            "messages for keywords and patterns indicating medical emergencies — "
            "such as chest pain, difficulty breathing, severe bleeding, loss of "
            "consciousness, suicidal thoughts, or any life-threatening symptoms. "
            "You err on the side of caution: if in doubt, trigger an alert. "
            "Speed is critical in emergencies."
        ),
        tools=[trigger_emergency_alert, search_patient_records, get_patient_info],
        llm=get_llm(temperature=0.1),
        verbose=True,
        allow_delegation=False,
    )
