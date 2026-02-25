"""CrewAI Tool: Query PostgreSQL for patient data."""
from crewai.tools import tool
from sqlalchemy import create_engine, text
from app.config.settings import settings


def _get_sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    return create_engine(url)


@tool("get_patient_info")
def get_patient_info(patient_id: int) -> str:
    """
    Get basic patient information from the database.

    Args:
        patient_id: The patient's database ID.

    Returns:
        Patient info including name, phone, and critical status.
    """
    engine = _get_sync_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, phone, emergency_contact, is_critical FROM patients WHERE id = :pid"),
            {"pid": patient_id},
        ).fetchone()

    if not row:
        return f"No patient found with ID {patient_id}."
    return (
        f"Patient: {row[1]}\n"
        f"Phone: {row[2]}\n"
        f"Emergency Contact: {row[3]}\n"
        f"Critical: {row[4]}"
    )


@tool("get_patient_prescriptions")
def get_patient_prescriptions(patient_id: int) -> str:
    """
    Get all active prescriptions for a patient.

    Args:
        patient_id: The patient's database ID.

    Returns:
        List of prescriptions with medicine name, dosage, and refill status.
    """
    engine = _get_sync_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT medicine_name, dosage, refill_allowed, expiry_date "
                "FROM prescriptions WHERE patient_id = :pid ORDER BY created_at DESC"
            ),
            {"pid": patient_id},
        ).fetchall()

    if not rows:
        return "No prescriptions found."

    lines = ["Current Prescriptions:"]
    for r in rows:
        refill = "Yes" if r[2] else "No"
        lines.append(f"- {r[0]} | Dosage: {r[1]} | Refill: {refill} | Expires: {r[3]}")
    return "\n".join(lines)


@tool("get_patient_appointments")
def get_patient_appointments(patient_id: int) -> str:
    """
    Get all appointments for a patient.

    Args:
        patient_id: The patient's database ID.

    Returns:
        List of appointments with doctor, date, and status.
    """
    engine = _get_sync_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT doctor_name, department, appointment_date, status, reason "
                "FROM appointments WHERE patient_id = :pid ORDER BY appointment_date DESC"
            ),
            {"pid": patient_id},
        ).fetchall()

    if not rows:
        return "No appointments found."

    lines = ["Appointments:"]
    for r in rows:
        lines.append(
            f"- Dr. {r[0]} ({r[1] or 'General'}) | {r[2]} | Status: {r[3]} | Reason: {r[4] or 'N/A'}"
        )
    return "\n".join(lines)
