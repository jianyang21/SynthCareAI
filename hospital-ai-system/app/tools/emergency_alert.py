"""CrewAI Tool: Emergency alerts via Telegram to hospital and contacts."""
from crewai.tools import tool
from sqlalchemy import create_engine, text
import httpx

from app.config.settings import settings
from app.core.logger import logger


def _get_sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    return create_engine(url)


def _send_telegram_alert(chat_id: str, message: str) -> bool:
    """Send Telegram message via Bot API. Returns True on success."""
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.warning("telegram_alert_not_configured", chat_id=chat_id)
        return False
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = httpx.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
        resp.raise_for_status()
        logger.info("telegram_alert_sent", chat_id=chat_id)
        return True
    except Exception as exc:
        logger.error("telegram_alert_failed", chat_id=chat_id, error=str(exc))
        return False


@tool("trigger_emergency_alert")
def trigger_emergency_alert(patient_id: int, reason: str) -> str:
    """
    Trigger an emergency alert for a patient. Notifies the hospital
    and the patient's emergency contacts (friends/family) via Telegram.

    Args:
        patient_id: The patient's database ID.
        reason: Description of the emergency or abnormality detected.

    Returns:
        Summary of who was notified.
    """
    engine = _get_sync_engine()

    # Get patient info
    with engine.connect() as conn:
        patient = conn.execute(
            text("SELECT name, phone, telegram_id FROM patients WHERE id = :pid"),
            {"pid": patient_id},
        ).fetchone()

        contacts = conn.execute(
            text("SELECT name, phone, telegram_id FROM emergency_contacts WHERE patient_id = :pid"),
            {"pid": patient_id},
        ).fetchall()

    if not patient:
        return f"Patient {patient_id} not found."

    patient_name = patient[0]
    notified = []

    # Notify hospital via Telegram
    if settings.HOSPITAL_TELEGRAM_ID:
        hospital_msg = (
            f"🚨 *EMERGENCY ALERT*\n"
            f"Patient: {patient_name} (ID: {patient_id})\n"
            f"Reason: {reason}\n"
            f"Immediate attention required!"
        )
        if _send_telegram_alert(settings.HOSPITAL_TELEGRAM_ID, hospital_msg):
            notified.append("Hospital")

    # Notify emergency contacts (friends/family) via Telegram
    for contact in contacts:
        contact_name, _, tg_id = contact
        if tg_id:
            contact_msg = (
                f"🚨 *EMERGENCY ALERT for {patient_name}*\n"
                f"Reason: {reason}\n"
                f"Please contact the hospital immediately."
            )
            if _send_telegram_alert(tg_id, contact_msg):
                notified.append(contact_name)

    # Mark patient as critical in the system
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE patients SET is_critical = TRUE WHERE id = :pid"),
            {"pid": patient_id},
        )
        conn.commit()

    logger.info("emergency_triggered", patient_id=patient_id, reason=reason, notified=notified)

    if notified:
        return f"🚨 Emergency alert sent for {patient_name}!\nNotified via Telegram: {', '.join(notified)}"
    else:
        return (
            f"⚠️ Emergency flagged for {patient_name}, but no Telegram contacts could be reached. "
            f"Patient marked as critical in system. Reason: {reason}"
        )
