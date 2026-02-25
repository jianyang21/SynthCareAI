"""CrewAI Tool: Book, reschedule, or cancel appointments."""
from datetime import datetime
from crewai.tools import tool
from sqlalchemy import create_engine, text
from app.config.settings import settings
from app.core.logger import logger


def _get_sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    return create_engine(url)


@tool("book_appointment")
def book_appointment(
    patient_id: int,
    doctor_name: str,
    department: str,
    appointment_date: str,
    reason: str,
) -> str:
    """
    Book a new appointment for the patient.

    Args:
        patient_id: The patient's database ID.
        doctor_name: Name of the doctor.
        department: Department (e.g., Cardiology, General).
        appointment_date: Date and time in ISO format (YYYY-MM-DD HH:MM).
        reason: Reason for the appointment.

    Returns:
        Confirmation message with appointment details.
    """
    try:
        dt = datetime.fromisoformat(appointment_date)
    except ValueError:
        return f"Invalid date format: {appointment_date}. Use YYYY-MM-DD HH:MM."

    engine = _get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "INSERT INTO appointments (patient_id, doctor_name, department, appointment_date, reason, status) "
                "VALUES (:pid, :doc, :dept, :dt, :reason, 'scheduled') RETURNING id"
            ),
            {
                "pid": patient_id,
                "doc": doctor_name,
                "dept": department,
                "dt": dt,
                "reason": reason,
            },
        )
        conn.commit()
        appt_id = result.fetchone()[0]

    logger.info("appointment_booked", appointment_id=appt_id, patient_id=patient_id)
    return (
        f"✅ Appointment booked successfully!\n"
        f"ID: {appt_id}\n"
        f"Doctor: Dr. {doctor_name} ({department})\n"
        f"Date: {dt.strftime('%B %d, %Y at %I:%M %p')}\n"
        f"Reason: {reason}"
    )


@tool("cancel_appointment")
def cancel_appointment(appointment_id: int) -> str:
    """
    Cancel an existing appointment.

    Args:
        appointment_id: The appointment ID to cancel.

    Returns:
        Confirmation that the appointment was cancelled.
    """
    engine = _get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE appointments SET status = 'cancelled' WHERE id = :aid AND status = 'scheduled' RETURNING id"),
            {"aid": appointment_id},
        )
        conn.commit()
        row = result.fetchone()

    if not row:
        return f"Appointment {appointment_id} not found or already cancelled."

    logger.info("appointment_cancelled", appointment_id=appointment_id)
    return f"✅ Appointment {appointment_id} has been cancelled."
