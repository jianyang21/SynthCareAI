"""CrewAI Tool: Order medicines from a prescription."""
import json
from crewai.tools import tool
from sqlalchemy import create_engine, text
from app.config.settings import settings
from app.core.logger import logger


def _get_sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    return create_engine(url)


@tool("order_medicines")
def order_medicines(
    patient_id: int,
    medicines_json: str,
    delivery_address: str = "",
) -> str:
    """
    Place a medicine order for the patient.

    Args:
        patient_id: The patient's database ID.
        medicines_json: JSON string of medicines list, e.g. '[{"name": "Paracetamol", "qty": 2, "dosage": "500mg"}]'
        delivery_address: Optional delivery address.

    Returns:
        Confirmation message with order details.
    """
    try:
        medicines = json.loads(medicines_json)
    except json.JSONDecodeError:
        return "Invalid medicines JSON format. Expected: [{\"name\": \"...\", \"qty\": 1, \"dosage\": \"...\"}]"

    if not medicines:
        return "No medicines specified in the order."

    engine = _get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "INSERT INTO medicine_orders (patient_id, medicines, status, delivery_address) "
                "VALUES (:pid, :meds, 'pending', :addr) RETURNING id"
            ),
            {
                "pid": patient_id,
                "meds": json.dumps(medicines),
                "addr": delivery_address or "Pickup at hospital pharmacy",
            },
        )
        conn.commit()
        order_id = result.fetchone()[0]

    med_list = "\n".join(
        f"  - {m['name']} x{m.get('qty', 1)} ({m.get('dosage', 'N/A')})"
        for m in medicines
    )

    logger.info("medicine_ordered", order_id=order_id, patient_id=patient_id)
    return (
        f"✅ Medicine order placed!\n"
        f"Order ID: {order_id}\n"
        f"Medicines:\n{med_list}\n"
        f"Delivery: {delivery_address or 'Pickup at hospital pharmacy'}\n"
        f"Status: Pending"
    )


@tool("get_order_status")
def get_order_status(order_id: int) -> str:
    """
    Check the status of a medicine order.

    Args:
        order_id: The order ID to check.

    Returns:
        Current status of the medicine order.
    """
    engine = _get_sync_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, medicines, status, delivery_address, ordered_at FROM medicine_orders WHERE id = :oid"),
            {"oid": order_id},
        ).fetchone()

    if not row:
        return f"Order {order_id} not found."

    medicines = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    med_list = ", ".join(m["name"] for m in medicines)
    return (
        f"Order #{row[0]}\n"
        f"Medicines: {med_list}\n"
        f"Status: {row[2]}\n"
        f"Delivery: {row[3]}\n"
        f"Ordered: {row[4]}"
    )
