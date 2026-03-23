"""
SynthCare Agent — Tool Registry & System Prompt
------------------------------------------------
This file owns:
  - HTTP helpers (_get, _post)
  - All @tool definitions
  - TOOLS list
  - SYSTEM_PROMPT

It does NOT run any agent loop.
brain.py is the single entry point for all conversations.
"""

import os
import json
import requests
from typing import Any

from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# =========================================================
# HTTP HELPERS
# =========================================================

def _post(path: str, payload: dict) -> Any:
    try:
        r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return {"error": detail}
    except Exception as e:
        return {"error": str(e)}


def _get(path: str, params: dict = None) -> Any:
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return {"error": detail}
    except Exception as e:
        return {"error": str(e)}


# =========================================================
# TOOLS
# =========================================================

@tool
def get_database_schema() -> str:
    """
    Get the full database schema — all tables and their column names and types.
    Call this first when unsure of field names before querying or creating records.
    """
    result = _get("/schema")
    return json.dumps(result, indent=2)


@tool
def query_records(table: str, filters: str = "{}") -> str:
    """
    Query (search/list/find) records from a database table.

    Args:
        table: One of: patients, doctors, appointments, medicines,
               medicine_inventory, prescriptions, prescription_items,
               patient_orders, patient_order_items
        filters: JSON string of field filters. Examples:
                 '{"first_name": "Abhinav"}'
                 '{"status": "scheduled"}'
                 '{"city": "LIKE %Mumbai%"}'
                 '{}' → returns all records (up to 100)

    Returns: JSON list of matching records.
    """
    try:
        filters_dict = json.loads(filters) if isinstance(filters, str) else filters
    except json.JSONDecodeError:
        return json.dumps({"error": f"Invalid JSON filters: {filters}"})
    result = _post("/query", {"table": table, "filters": filters_dict})
    return json.dumps(result, indent=2, default=str)


@tool
def create_record(table: str, data: str) -> str:
    """
    Create a NEW record in the database.
    ONLY use this to add brand new records — never to update existing ones.

    Args:
        table: Table name (patients, doctors, appointments, medicines, etc.)
        data: JSON string of field values. Examples:
              Patients: '{"first_name": "John", "last_name": "Doe", "gender": "Male",
                          "email": "john@example.com", "phone": "9876543210",
                          "city": "Hyderabad", "blood_group": "O+"}'
              Doctors:  '{"first_name": "Abhinav", "last_name": "Lella",
                          "specialization": "Oncology"}'
              Appointments: '{"patient_id": 1, "doctor_id": 1,
                              "appointment_date": "2025-04-01T10:00:00",
                              "status": "scheduled"}'

    Returns: The created record with its assigned ID.
    """
    try:
        data_dict = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        return json.dumps({"error": f"Invalid JSON data: {data}"})
    result = _post("/create", {"table": table, "data": data_dict})
    return json.dumps(result, indent=2, default=str)


@tool
def update_record(table: str, filters: str, data: str) -> str:
    """
    Update existing records in the database.
    Use this when the user says: update, edit, modify, change, rename, set, correct.
    NEVER call create_record to update — always use this tool for modifications.

    Args:
        table: Table name (patients, doctors, appointments, etc.)
        filters: JSON string to identify which records to update.
                 Example: '{"first_name": "Abhinav"}' or '{"id": 1}'
        data: JSON string of fields and new values to set.
              Example: '{"last_name": "Lella", "specialization": "Cardiology"}'

    Returns: Updated record(s) with the new values.
    """
    try:
        filters_dict = json.loads(filters) if isinstance(filters, str) else filters
        data_dict    = json.loads(data)    if isinstance(data, str)    else data
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})
    result = _post("/update", {"table": table, "filters": filters_dict, "data": data_dict})
    return json.dumps(result, indent=2, default=str)


@tool
def delete_record(table: str, filters: str) -> str:
    """
    Delete records from the database.
    Use this when the user says: delete, remove, drop, erase, get rid of.
    Always confirm you have the right filter before deleting.

    Args:
        table: Table name (patients, doctors, appointments, etc.)
        filters: JSON string to identify which records to delete.
                 Example: '{"id": 2}' or '{"first_name": "John", "last_name": "Doe"}'
                 At least one filter is required — will not delete without a filter.

    Returns: Count and details of deleted records.
    """
    try:
        filters_dict = json.loads(filters) if isinstance(filters, str) else filters
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON filters: {e}"})
    if not filters_dict:
        return json.dumps({"error": "Filters cannot be empty for delete — too dangerous"})
    result = _post("/delete", {"table": table, "filters": filters_dict})
    return json.dumps(result, indent=2, default=str)


@tool
def get_patient_appointments(limit: int = 50) -> str:
    """
    Get a joined list of all appointments with patient name, doctor name,
    doctor specialization, appointment date and status.

    Args:
        limit: Max records to return (default 50)
    """
    result = _get("/joins/patient-appointments", params={"limit": limit})
    return json.dumps(result, indent=2, default=str)

@tool
def get_prescription_details(prescription_id: int = None, patient_id: int = None) -> str:
    """
    Get full prescription details — patient, doctor, and ALL medicines
    with dosage, frequency, and duration in a single joined result.

    Use this instead of querying prescription_items separately.

    Args:
        prescription_id: filter by specific prescription (optional)
        patient_id: filter by patient (optional)
    """
    params = {}
    if prescription_id:
        params["prescription_id"] = prescription_id
    if patient_id:
        params["patient_id"] = patient_id
    result = _get("/joins/prescription-details", params=params)
    return json.dumps(result, indent=2, default=str)
@tool
def get_patient_orders(limit: int = 50) -> str:
    """
    Get all patient medication orders with medicine name and quantities.

    Args:
        limit: Max records to return (default 50)
    """
    result = _get("/joins/patient-orders", params={"limit": limit})
    return json.dumps(result, indent=2, default=str)


@tool
def generate_prescription_order(prescription_id: int) -> str:
    """
    Generate a medication order from a prescription.
    Calculates quantities (frequency_per_day × duration_days), creates the order,
    deducts stock from inventory, and marks the prescription as processed.

    Args:
        prescription_id: The ID of the prescription.
    """
    result = _post(f"/prescriptions/{prescription_id}/generate-order", {})
    return json.dumps(result, indent=2)


@tool
def get_low_stock_medicines() -> str:
    """
    Get all medicines that are at or below their reorder level.
    Use this to check which medicines need restocking.
    """
    result = _get("/inventory/low-stock")
    return json.dumps(result, indent=2)


@tool
def get_dashboard_analytics() -> str:
    """
    Get hospital analytics: total patients, doctors, appointments, prescriptions,
    total revenue, and pending orders count.
    """
    result = _get("/analytics/dashboard")
    return json.dumps(result, indent=2)


@tool
def search_medical_records(patient_id: int, query: str) -> str:
    """
    Search a patient's medical records (PDFs, reports, doctor notes).

    Use this for:
    - lab results, blood reports, medical history, doctor notes
    - any health-related question about a specific patient

    Args:
        patient_id: ID of the patient
        query: what to search (e.g. "hemoglobin", "blood pressure")

    Returns: Relevant text chunks. MUST be used to answer — do NOT ignore.
    """
    result = _post("/records/search", {
        "patient_id": patient_id,
        "query": query
    })
    return json.dumps(result, indent=2)


@tool
def add_medical_note(patient_id: int, text: str) -> str:
    """
    Add a doctor's note or medical observation for a patient.

    Args:
        patient_id: ID of patient
        text: note content
    """
    result = _post("/records/add-note", {
        "patient_id": patient_id,
        "text": text
    })
    return json.dumps(result, indent=2)


@tool
def add_medical_comment(patient_id: int, comment: str) -> str:
    """
    Add a short medical comment or remark.

    Args:
        patient_id: ID of patient
        comment: short note
    """
    result = _post("/records/comment", {
        "patient_id": patient_id,
        "comment": comment
    })
    return json.dumps(result, indent=2)


@tool
def find_patient_id(name: str) -> str:
    """
    Find patient ID by name.
    Use this BEFORE searching medical records if patient_id is unknown.
    """
    result = _post("/query", {
        "table": "patients",
        "filters": {"first_name": name}
    })
    return json.dumps(result, indent=2)


# =========================================================
# TOOL REGISTRY  (imported by brain.py)
# =========================================================

TOOLS = [
    get_database_schema,
    query_records,
    create_record,
    update_record,
    delete_record,
    get_patient_appointments,
    get_patient_orders,
    generate_prescription_order,
    get_low_stock_medicines,
    get_dashboard_analytics,
    search_medical_records,
    add_medical_note,
    add_medical_comment,
    find_patient_id,
]


# =========================================================
# SYSTEM PROMPT  (imported by brain.py)
# =========================================================

SYSTEM_PROMPT = """You are SynthCare AI, a smart healthcare management assistant with full database access.

You can CREATE, READ, UPDATE, and DELETE records using your tools.

STRICT RULES — follow these exactly:
1. To add something new        → use create_record
2. To find / list / show       → use query_records (or the specialised join tools)
3. To modify / update / edit   → use update_record  (NEVER create_record)
4. To remove / delete / erase  → use delete_record
5. Never guess data            → always fetch with query_records first if you need an ID
6. Present results clearly     → bullet points or a table

AVAILABLE TABLES:
patients, doctors, appointments, medicines, medicine_inventory,
prescriptions, prescription_items, patient_orders, patient_order_items

MEDICAL RECORDS (RAG):
- Use search_medical_records to answer ANY health-related question
- If patient_id is unknown → call query_records FIRST to find it
- If search_medical_records returns empty → say "No medical data found", do NOT guess
APPOINTMENT QUERIES:
- appointments table has NO name columns — only patient_id and doctor_id
- ALWAYS query patients first to get patient_id, THEN query appointments
- NEVER query appointments directly by name

JOIN TOOLS — always prefer these over manual chaining:
- get_patient_appointments()     → appointments with patient + doctor names
- get_prescription_details()     → prescriptions WITH medicine names in one call
- get_patient_orders()           → orders with medicine names
Use these BEFORE falling back to query_records for these topics.
```

---

**Summary of what to do right now:**
```
1. Clear DB with the SQL above
2. Seed once via the button
3. Add the 2 system prompt rules to agent.py
4. Add get_prescription_details tool to agent.py + TOOLS list
5. Add /joins/prescription-details endpoint to main.py

FIELD FORMATS:
- Dates:     YYYY-MM-DD
- DateTimes: YYYY-MM-DDTHH:MM:SS
- IDs are integers
"""