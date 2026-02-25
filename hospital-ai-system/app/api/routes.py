"""
FastAPI API routes for the Hospital AI System.

Provides REST endpoints for EHR ingestion, chat, appointments,
medicine ordering, and the Telegram webhook.
"""
import os
import json
import tempfile
import asyncio
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from pydantic import BaseModel

from app.core.logger import logger
from app.agents.crew import classify_and_route, run_medical_qa
from app.telegram.memory import save_message, get_chat_history_text

router = APIRouter()


# ──────────────────────  Request/Response Models  ──────────────────────


class ChatRequest(BaseModel):
    patient_id: int
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: str = ""


class AppointmentRequest(BaseModel):
    patient_id: int
    doctor_name: str
    department: str = "General"
    appointment_date: str  # ISO format
    reason: str = ""


class MedicineOrderRequest(BaseModel):
    patient_id: int
    medicines: list[dict]  # [{"name": "...", "qty": 1, "dosage": "..."}]
    delivery_address: str = ""


# ──────────────────────  EHR Ingestion  ──────────────────────


@router.post("/api/ingest")
async def ingest_ehr(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
):
    """Upload and ingest an EHR PDF document."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        from app.rag.ingestion import ingest_pdf
        result = await asyncio.to_thread(
            ingest_pdf, tmp_path, patient_id, file.filename
        )
        return {"status": "success", "filename": file.filename, **result}

    except Exception as exc:
        logger.error("ingest_failed", error=str(exc))
        raise HTTPException(500, f"Ingestion failed: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ──────────────────────  Chat  ──────────────────────


@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chat endpoint — routes through CrewAI agents."""
    chat_history = get_chat_history_text(req.patient_id, count=6)
    response = await asyncio.to_thread(
        classify_and_route, req.message, req.patient_id, chat_history
    )
    save_message(req.patient_id, "user", req.message)
    save_message(req.patient_id, "assistant", response)
    return ChatResponse(response=response)


# ──────────────────────  Appointments  ──────────────────────


@router.get("/api/appointments/{patient_id}")
async def list_appointments(patient_id: int):
    """List all appointments for a patient."""
    from app.tools.db_query import get_patient_appointments
    result = get_patient_appointments.run(patient_id=patient_id)
    return {"patient_id": patient_id, "appointments": result}


@router.post("/api/appointments")
async def create_appointment(req: AppointmentRequest):
    """Book a new appointment."""
    from app.tools.appointment_booking import book_appointment
    result = book_appointment.run(
        patient_id=req.patient_id,
        doctor_name=req.doctor_name,
        department=req.department,
        appointment_date=req.appointment_date,
        reason=req.reason,
    )
    return {"status": "success", "details": result}


# ──────────────────────  Medicine Orders  ──────────────────────


@router.post("/api/medicine/order")
async def order_medicine(req: MedicineOrderRequest):
    """Place a medicine order."""
    from app.tools.medicine_ordering import order_medicines
    result = order_medicines.run(
        patient_id=req.patient_id,
        medicines_json=json.dumps(req.medicines),
        delivery_address=req.delivery_address,
    )
    return {"status": "success", "details": result}


# ──────────────────────  Telegram Webhook  ──────────────────────


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram updates via webhook."""
    from app.telegram.bot import telegram_app

    if telegram_app is None:
        raise HTTPException(503, "Telegram bot not configured.")

    data = await request.json()
    update = telegram_app.update_queue
    from telegram import Update as TGUpdate
    tg_update = TGUpdate.de_json(data, telegram_app.bot)
    await telegram_app.process_update(tg_update)
    return {"ok": True}
