"""
CrewAI Crew Orchestrator — Assembles agents and runs tasks.

Uses the centralized LLM provider (Ollama → Gemini fallback).
"""
from crewai import Task, Crew, Process

from app.agents.triage_agent import create_triage_agent
from app.agents.medical_qa import create_medical_qa_agent
from app.agents.appointment_agent import create_appointment_agent
from app.agents.medicine_agent import create_medicine_agent
from app.agents.emergency_agent import create_emergency_agent
from app.core.logger import logger


def run_medical_qa(query: str, patient_id: int, chat_history: str = "") -> str:
    """Run the Medical QA flow for a patient question."""
    agent = create_medical_qa_agent()
    task = Task(
        description=(
            f"Answer the following patient question using their medical records.\n"
            f"Patient ID: {patient_id}\n"
            f"Previous conversation:\n{chat_history}\n\n"
            f"Patient's question: {query}"
        ),
        expected_output="A clear, accurate, and empathetic answer based on the patient's medical records.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return str(result)


def run_appointment_booking(query: str, patient_id: int) -> str:
    """Run the Appointment booking flow."""
    agent = create_appointment_agent()
    task = Task(
        description=(
            f"Help the patient with their appointment request.\n"
            f"Patient ID: {patient_id}\n"
            f"Patient's request: {query}"
        ),
        expected_output="Confirmation of the appointment action taken (booked, cancelled, or list of appointments).",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return str(result)


def run_medicine_ordering(query: str, patient_id: int) -> str:
    """Run the Medicine ordering flow."""
    agent = create_medicine_agent()
    task = Task(
        description=(
            f"Help the patient order medicines based on their prescription.\n"
            f"Patient ID: {patient_id}\n"
            f"Patient's request: {query}"
        ),
        expected_output="Confirmation of medicine order or extracted prescription details for review.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return str(result)


def run_emergency_check(message: str, patient_id: int) -> str:
    """Run emergency detection on a patient message."""
    agent = create_emergency_agent()
    task = Task(
        description=(
            f"Analyze this patient message for any emergency or abnormality.\n"
            f"Patient ID: {patient_id}\n"
            f"Message: {message}\n\n"
            f"If this is a genuine emergency, trigger alerts immediately. "
            f"If not, state that no emergency was detected."
        ),
        expected_output="Either an emergency alert confirmation or a statement that no emergency was detected.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return str(result)


def classify_and_route(message: str, patient_id: int, chat_history: str = "") -> str:
    """
    Main entry point: Classify the patient's message and route to
    the appropriate agent crew.
    """
    logger.info("crew_classify_start", patient_id=patient_id, message=message[:100])

    # Step 1: Classify intent using Triage Agent
    triage = create_triage_agent()
    classify_task = Task(
        description=(
            f"Classify this patient message into exactly ONE category.\n"
            f"Message: \"{message}\"\n\n"
            f"Reply with ONLY the category name: "
            f"MEDICAL_QA, APPOINTMENT, MEDICINE, EMERGENCY, or GENERAL."
        ),
        expected_output="One word: MEDICAL_QA, APPOINTMENT, MEDICINE, EMERGENCY, or GENERAL.",
        agent=triage,
    )
    crew = Crew(agents=[triage], tasks=[classify_task], process=Process.sequential, verbose=True)
    intent_raw = str(crew.kickoff()).strip().upper()

    logger.info("crew_classified", intent=intent_raw, patient_id=patient_id)

    # Step 2: Route to appropriate specialist
    if "EMERGENCY" in intent_raw:
        return run_emergency_check(message, patient_id)
    elif "APPOINTMENT" in intent_raw:
        return run_appointment_booking(message, patient_id)
    elif "MEDICINE" in intent_raw:
        return run_medicine_ordering(message, patient_id)
    elif "MEDICAL" in intent_raw or "QA" in intent_raw:
        return run_medical_qa(message, patient_id, chat_history)
    else:
        # GENERAL — answer with QA agent for a friendly response
        return run_medical_qa(message, patient_id, chat_history)
