from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


# ─────────────────────────  Patient & EHR  ─────────────────────────


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    telegram_id = Column(String, nullable=True, unique=True)
    emergency_contact = Column(String)
    is_critical = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    prescriptions = relationship("Prescription", back_populates="patient")
    ehr_documents = relationship("EHRDocument", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    medicine_orders = relationship("MedicineOrder", back_populates="patient")
    conversations = relationship("ConversationMessage", back_populates="patient")
    emergency_contacts = relationship("EmergencyContact", back_populates="patient")


class EHRDocument(Base):
    __tablename__ = "ehr_documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="ehr_documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """PostgreSQL fallback storage for RAG document chunks."""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("ehr_documents.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, nullable=True)
    qdrant_point_id = Column(String, nullable=True)

    document = relationship("EHRDocument", back_populates="chunks")


# ─────────────────────────  Prescriptions  ─────────────────────────


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medicine_name = Column(String, nullable=False)
    dosage = Column(String)
    refill_allowed = Column(Boolean, default=True)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="prescriptions")


# ─────────────────────────  Appointments  ─────────────────────────


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="appointments")


# ─────────────────────────  Medicine Orders  ─────────────────────────


class MedicineOrder(Base):
    __tablename__ = "medicine_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    medicines = Column(JSON, nullable=False)  # [{"name": "...", "qty": 1, "dosage": "..."}]
    total_price = Column(Float, nullable=True)
    status = Column(String, default="pending")  # pending, confirmed, dispatched, delivered
    delivery_address = Column(Text, nullable=True)
    ordered_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="medicine_orders")


# ─────────────────────────  Conversation Memory  ─────────────────────────


class ConversationMessage(Base):
    """Long-term chat memory stored in PostgreSQL."""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="conversations")


# ─────────────────────────  Emergency Contacts  ─────────────────────────


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    telegram_id = Column(String, nullable=True)
    relationship_type = Column(String, nullable=True)  # spouse, parent, sibling, friend

    patient = relationship("Patient", back_populates="emergency_contacts")
