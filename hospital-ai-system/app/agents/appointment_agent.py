"""Appointment Agent — Schedules, manages doctor appointments."""
from crewai import Agent
from app.core.llm_provider import get_llm
from app.tools.appointment_booking import book_appointment, cancel_appointment
from app.tools.db_query import get_patient_appointments


def create_appointment_agent() -> Agent:
    return Agent(
        role="Appointment Scheduling Specialist",
        goal=(
            "Help patients schedule, reschedule, or cancel appointments with "
            "doctors. Ensure appointments are booked at convenient times and "
            "provide all necessary details."
        ),
        backstory=(
            "You are the hospital's appointment scheduling specialist. You know "
            "all departments and doctors, and you help patients book appointments "
            "efficiently. You always confirm appointment details before finalizing."
        ),
        tools=[book_appointment, cancel_appointment, get_patient_appointments],
        llm=get_llm(temperature=0.2),
        verbose=True,
        allow_delegation=False,
    )
