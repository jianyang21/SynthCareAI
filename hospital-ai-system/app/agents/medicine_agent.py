"""Medicine Booking Agent — Parses prescriptions and orders medicines."""
from crewai import Agent
from app.core.llm_provider import get_llm
from app.tools.medicine_ordering import order_medicines, get_order_status
from app.tools.prescription_parser import parse_prescription
from app.tools.db_query import get_patient_prescriptions


def create_medicine_agent() -> Agent:
    return Agent(
        role="Medicine Booking Specialist",
        goal=(
            "Help patients order medicines based on their prescriptions. "
            "Parse prescriptions to extract medicine details, verify with the "
            "patient, and place orders through the pharmacy system."
        ),
        backstory=(
            "You are a pharmacy specialist who helps patients order their "
            "prescribed medicines. You carefully review prescriptions, extract "
            "medicine names, dosages, and quantities, and ensure orders are "
            "accurate before confirming. You always verify with the patient "
            "before placing an order."
        ),
        tools=[order_medicines, get_order_status, parse_prescription, get_patient_prescriptions],
        llm=get_llm(temperature=0.2),
        verbose=True,
        allow_delegation=False,
    )
