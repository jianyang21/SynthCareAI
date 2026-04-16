from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import create_engine, Column, Integer, BigInteger, Text, Date, DateTime, ForeignKey, Numeric, func, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime, date, timedelta
from typing import Dict, Any
from pydantic import BaseModel
import re
import os
import random
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

# Import the logic from your new service file
from backend.core_api.pdf_service import process_and_index_pdf, answer_pdf_question

from backend.rag_agent.vector_store import (
    store_pdf_hybrid,
    store_text_hybrid,
    search_hybrid,
    add_comment_hybrid,
)

from fastapi.middleware.cors import CORSMiddleware



DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://abhinav:password@localhost:5432/synthcare")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# MODELS  (synced to actual DB schema)
# ==========================================

class Patient(Base):
    __tablename__ = "patients"
    id                             = Column(BigInteger, primary_key=True, autoincrement=True)
    first_name                     = Column(Text)
    last_name                      = Column(Text)
    gender                         = Column(Text)
    date_of_birth                  = Column(Date)
    email                          = Column(Text)
    phone                          = Column(Text)
    city                           = Column(Text)
    state                          = Column(Text)
    country                        = Column(Text)
    address_line1                  = Column(Text)
    address_line2                  = Column(Text)
    postal_code                    = Column(Text)
    blood_group                    = Column(Text)
    emergency_contact_name         = Column(Text)
    emergency_contact_phone        = Column(Text)
    emergency_contact_relationship = Column(Text)
    deleted_at                     = Column(DateTime, nullable=True)
    created_at                     = Column(DateTime, default=datetime.utcnow)
    updated_at                     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    appointments  = relationship("Appointment",  cascade="all, delete")
    prescriptions = relationship("Prescription", cascade="all, delete")


class Doctor(Base):
    __tablename__ = "doctors"
    id             = Column(BigInteger, primary_key=True, autoincrement=True)
    first_name     = Column(Text)
    last_name      = Column(Text)
    specialization = Column(Text)
    email          = Column(Text)
    phone          = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    appointments   = relationship("Appointment", cascade="all, delete")


class Appointment(Base):
    __tablename__ = "appointments"
    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id       = Column(BigInteger, ForeignKey("patients.id"))
    doctor_id        = Column(BigInteger, ForeignKey("doctors.id"))
    appointment_date = Column(DateTime)
    status           = Column(Text)
    notes            = Column(Text)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Index("idx_appt_patient", Appointment.patient_id)
Index("idx_appt_doctor",  Appointment.doctor_id)


class Medicine(Base):
    __tablename__ = "medicines"
    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    name         = Column(Text)
    generic_name = Column(Text)
    strength     = Column(Text)
    dosage_form  = Column(Text)
    manufacturer = Column(Text)
    unit_price   = Column(Numeric)
    created_at   = Column(DateTime, default=datetime.utcnow)


class MedicineInventory(Base):
    __tablename__ = "medicine_inventory"
    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    medicine_id   = Column(BigInteger, ForeignKey("medicines.id"))
    quantity      = Column(Integer)
    reorder_level = Column(Integer)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Index("idx_inventory_med", MedicineInventory.medicine_id)


class Prescription(Base):
    __tablename__ = "prescriptions"
    id             = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id     = Column(BigInteger, ForeignKey("patients.id"))
    doctor_id      = Column(BigInteger, ForeignKey("doctors.id"))
    appointment_id = Column(BigInteger, ForeignKey("appointments.id"), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    items          = relationship("PrescriptionItem", cascade="all, delete", back_populates="prescription")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    id                = Column(BigInteger, primary_key=True, autoincrement=True)
    prescription_id   = Column(BigInteger, ForeignKey("prescriptions.id"))
    medicine_id       = Column(BigInteger, ForeignKey("medicines.id"))
    frequency_per_day = Column(Integer)
    frequency         = Column(Text)
    duration_days     = Column(Integer)
    duration          = Column(Text)
    dosage            = Column(Text)
    instructions      = Column(Text)
    prescription      = relationship("Prescription", back_populates="items")


Index("idx_prescription_item", PrescriptionItem.prescription_id)


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id             = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id     = Column(BigInteger, ForeignKey("patients.id"))
    doctor_id      = Column(BigInteger, ForeignKey("doctors.id"))
    appointment_id = Column(BigInteger, ForeignKey("appointments.id"), nullable=True)
    symptoms       = Column(Text)
    diagnosis      = Column(Text)
    treatment_plan = Column(Text)
    notes          = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)


class PatientOrder(Base):
    __tablename__ = "patient_orders"
    id              = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id      = Column(BigInteger)
    prescription_id = Column(BigInteger)
    order_status    = Column(Text)
    created_at      = Column(DateTime, default=datetime.utcnow)


class PatientOrderItem(Base):
    __tablename__ = "patient_order_items"
    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id    = Column(BigInteger)
    medicine_id = Column(BigInteger)
    quantity    = Column(Integer)
    unit_price  = Column(Numeric)


# NOTE: create_all commented out — DB already exists, schema managed manually
# Base.metadata.create_all(engine)


# ==========================================
# REQUEST MODELS
# ==========================================

class CreateRequest(BaseModel):
    table: str
    data: Dict[str, Any]

class QueryRequest(BaseModel):
    table: str
    filters: Dict[str, Any] = {}

class UpdateRequest(BaseModel):
    table: str
    filters: Dict[str, Any]
    data: Dict[str, Any]

class DeleteRequest(BaseModel):
    table: str
    filters: Dict[str, Any]

class NoteRequest(BaseModel):
    patient_id: int
    text: str

class SearchRequest(BaseModel):
    patient_id: int
    query: str

class CommentRequest(BaseModel):
    patient_id: int
    comment: str


# ==========================================
# HELPERS
# ==========================================

TABLE_MAP = {
    "patients":            Patient,
    "doctors":             Doctor,
    "appointments":        Appointment,
    "medicines":           Medicine,
    "medicine_inventory":  MedicineInventory,
    "prescriptions":       Prescription,
    "prescription_items":  PrescriptionItem,
    "medical_records":     MedicalRecord,
    "patient_orders":      PatientOrder,
    "patient_order_items": PatientOrderItem,
}


def serialize(obj):
    if obj is None:
        return None
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if hasattr(val, "isoformat"):
            result[col.name] = val.isoformat()
        elif hasattr(val, "__float__"):
            result[col.name] = float(val)
        else:
            result[col.name] = val
    return result


def apply_filters(q, model, filters: Dict[str, Any]):
    for key, val in filters.items():
        if not hasattr(model, key):
            continue
        column = getattr(model, key)
        if isinstance(val, str):
            match = re.match(r"(>=|<=|>|<|LIKE)\s*(.*)", val)
            if match:
                op, value = match.groups()
                if op == ">":      q = q.filter(column > value)
                elif op == "<":    q = q.filter(column < value)
                elif op == ">=":   q = q.filter(column >= value)
                elif op == "<=":   q = q.filter(column <= value)
                elif op == "LIKE": q = q.filter(column.ilike(value))
                continue
        q = q.filter(column == val)
    return q


# ==========================================
# APP
# ==========================================

app = FastAPI(title="SynthCare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ==========================================
# CRUD ENDPOINTS
# ==========================================

@app.post("/create")
def create(req: CreateRequest, db: Session = Depends(get_db)):
    model = TABLE_MAP.get(req.table)
    if not model:
        raise HTTPException(400, f"Invalid table: {req.table}")
    obj = model(**req.data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return serialize(obj)


@app.post("/query")
def query(req: QueryRequest, db: Session = Depends(get_db)):
    model = TABLE_MAP.get(req.table)
    if not model:
        raise HTTPException(400, f"Invalid table: {req.table}")
    q = apply_filters(db.query(model), model, req.filters)
    return [serialize(r) for r in q.limit(100).all()]


@app.post("/update")
def update(req: UpdateRequest, db: Session = Depends(get_db)):
    model = TABLE_MAP.get(req.table)
    if not model:
        raise HTTPException(400, f"Invalid table: {req.table}")
    if not req.filters:
        raise HTTPException(400, "Filters required for update")

    records = apply_filters(db.query(model), model, req.filters).all()
    if not records:
        raise HTTPException(404, "No matching records found")

    for record in records:
        for key, val in req.data.items():
            if hasattr(record, key) and key != "id":
                setattr(record, key, val)
        if hasattr(record, "updated_at"):
            record.updated_at = datetime.utcnow()

    db.commit()
    for r in records:
        db.refresh(r)

    return {"updated_count": len(records), "records": [serialize(r) for r in records]}


@app.post("/delete")
def delete(req: DeleteRequest, db: Session = Depends(get_db)):
    model = TABLE_MAP.get(req.table)
    if not model:
        raise HTTPException(400, f"Invalid table: {req.table}")
    if not req.filters:
        raise HTTPException(400, "Filters required for delete — too dangerous without")

    records = apply_filters(db.query(model), model, req.filters).all()
    if not records:
        raise HTTPException(404, "No matching records found")

    deleted = [serialize(r) for r in records]
    for record in records:
        db.delete(record)
    db.commit()

    return {"deleted_count": len(deleted), "deleted_records": deleted}


# ==========================================
# JOIN ENDPOINTS
# ==========================================

@app.get("/joins/patient-appointments")
def patient_appointments(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(
        Patient.id.label("patient_id"),
        Patient.first_name.label("patient_first_name"),
        Patient.last_name.label("patient_last_name"),
        Doctor.first_name.label("doctor_first_name"),
        Doctor.last_name.label("doctor_last_name"),
        Doctor.specialization,
        Appointment.id.label("appointment_id"),
        Appointment.appointment_date,
        Appointment.status,
        Appointment.notes,
    ).join(Appointment, Patient.id == Appointment.patient_id)\
     .join(Doctor, Appointment.doctor_id == Doctor.id)\
     .limit(limit).all()
    return [dict(r._mapping) for r in rows]


@app.get("/joins/patient-orders")
def patient_orders(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(
        PatientOrder.id.label("order_id"),
        PatientOrder.order_status,
        Medicine.name.label("medicine_name"),
        PatientOrderItem.quantity,
        PatientOrderItem.unit_price,
    ).join(PatientOrderItem, PatientOrder.id == PatientOrderItem.order_id)\
     .join(Medicine, PatientOrderItem.medicine_id == Medicine.id)\
     .limit(limit).all()
    return [dict(r._mapping) for r in rows]


# ==========================================
# PRESCRIPTION ORDER GENERATION
# (no order_generated column — checks for existing order instead)
# ==========================================

@app.post("/prescriptions/{prescription_id}/generate-order")
def generate_order(prescription_id: int, db: Session = Depends(get_db)):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(404, "Prescription not found")

    existing = db.query(PatientOrder).filter(PatientOrder.prescription_id == prescription_id).first()
    if existing:
        raise HTTPException(400, f"Order already generated (order_id={existing.id})")

    order = PatientOrder(
        patient_id      = prescription.patient_id,
        prescription_id = prescription.id,
        order_status    = "pending",
    )
    db.add(order)
    db.flush()

    for item in prescription.items:
        qty = (item.frequency_per_day or 1) * (item.duration_days or 1)
        medicine = db.query(Medicine).filter(Medicine.id == item.medicine_id).first()
        if not medicine:
            continue
        db.add(PatientOrderItem(
            order_id    = order.id,
            medicine_id = item.medicine_id,
            quantity    = qty,
            unit_price  = medicine.unit_price,
        ))
        inventory = db.query(MedicineInventory).filter(
            MedicineInventory.medicine_id == item.medicine_id
        ).first()
        if inventory:
            inventory.quantity = max(0, inventory.quantity - qty)

    db.commit()
    return {"order_id": order.id, "status": "created", "patient_id": prescription.patient_id}


# ==========================================
# INVENTORY
# ==========================================

@app.get("/inventory/low-stock")
def low_stock(db: Session = Depends(get_db)):
    rows = db.query(
        Medicine.id.label("medicine_id"),
        Medicine.name,
        MedicineInventory.quantity,
        MedicineInventory.reorder_level,
    ).join(Medicine, MedicineInventory.medicine_id == Medicine.id)\
     .filter(MedicineInventory.quantity <= MedicineInventory.reorder_level)\
     .all()
    return [dict(r._mapping) for r in rows]


# ==========================================
# ANALYTICS
# ==========================================

@app.get("/analytics/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {
        "total_patients":      db.query(func.count(Patient.id)).scalar(),
        "total_doctors":       db.query(func.count(Doctor.id)).scalar(),
        "total_appointments":  db.query(func.count(Appointment.id)).scalar(),
        "total_prescriptions": db.query(func.count(Prescription.id)).scalar(),
        "total_revenue":       float(db.query(func.sum(PatientOrderItem.quantity * PatientOrderItem.unit_price)).scalar() or 0),
        "pending_orders":      db.query(func.count(PatientOrder.id)).filter(PatientOrder.order_status == "pending").scalar(),
    }


# ==========================================
# SCHEMA + HEALTH
# ==========================================

@app.get("/schema")
def get_schema():
    return {
        name: [{"name": col.name, "type": str(col.type)} for col in model.__table__.columns]
        for name, model in TABLE_MAP.items()
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ==========================================
# RAG / MEDICAL RECORDS  (fixed Pydantic body signatures)
# ==========================================

@app.post("/records/upload")
async def upload_record(
    patient_id:  int        = Form(...),
    record_type: str        = Form(...),
    file:        UploadFile = File(...),
):
    return store_pdf_hybrid(file.file, patient_id, record_type)


@app.post("/records/add-note")
def add_note(req: NoteRequest):
    return store_text_hybrid(req.text, req.patient_id)


@app.post("/records/search")
def search_records(req: SearchRequest):
    return search_hybrid(req.patient_id, req.query)


@app.post("/records/comment")
def add_comment(req: CommentRequest):
    return add_comment_hybrid(req.patient_id, req.comment)


# ==========================================
# SEED ENDPOINTS
# ==========================================

def _clear_all(db: Session):
    """Delete in FK-safe dependency order."""
    db.query(PatientOrderItem).delete()
    db.query(PatientOrder).delete()
    db.query(PrescriptionItem).delete()
    db.query(Prescription).delete()
    db.query(MedicalRecord).delete()
    db.query(MedicineInventory).delete()
    db.query(Medicine).delete()
    db.query(Appointment).delete()
    db.query(Doctor).delete()
    db.query(Patient).delete()
    db.commit()


@app.post("/seed/clear")
def seed_clear(db: Session = Depends(get_db)):
    _clear_all(db)
    return {"message": "All data cleared"}


@app.post("/seed/patients")
def seed_patients(db: Session = Depends(get_db)):
    patients = [
        Patient(first_name="Abhinav", last_name="Lella",  gender="Male",
                date_of_birth=date(1998, 5, 14), email="abhinav@example.com",
                phone="9000000001", city="Hyderabad", state="Telangana",
                country="India", blood_group="O+"),
        Patient(first_name="Priya",   last_name="Sharma", gender="Female",
                date_of_birth=date(1992, 3, 22),  email="priya@example.com",
                phone="9000000002", city="Mumbai",    state="Maharashtra",
                country="India", blood_group="B+"),
        Patient(first_name="Rahul",   last_name="Verma",  gender="Male",
                date_of_birth=date(1985, 11, 5),  email="rahul@example.com",
                phone="9000000003", city="Delhi",     state="Delhi",
                country="India", blood_group="A-"),
        Patient(first_name="Sneha",   last_name="Nair",   gender="Female",
                date_of_birth=date(2000, 7, 30),  email="sneha@example.com",
                phone="9000000004", city="Bangalore", state="Karnataka",
                country="India", blood_group="AB+"),
        Patient(first_name="Karthik", last_name="Reddy",  gender="Male",
                date_of_birth=date(1978, 1, 17),  email="karthik@example.com",
                phone="9000000005", city="Chennai",   state="Tamil Nadu",
                country="India", blood_group="O-"),
    ]
    db.add_all(patients)
    db.commit()
    return {"message": f"Seeded {len(patients)} patients"}


@app.post("/seed/doctors")
def seed_doctors(db: Session = Depends(get_db)):
    doctors = [
        Doctor(first_name="Meera",  last_name="Iyer",   specialization="Cardiology",
               email="meera@synthcare.com",  phone="8000000001"),
        Doctor(first_name="Arun",   last_name="Pillai", specialization="Neurology",
               email="arun@synthcare.com",   phone="8000000002"),
        Doctor(first_name="Sunita", last_name="Bose",   specialization="Oncology",
               email="sunita@synthcare.com", phone="8000000003"),
        Doctor(first_name="Vikram", last_name="Das",    specialization="Orthopedics",
               email="vikram@synthcare.com", phone="8000000004"),
        Doctor(first_name="Deepa",  last_name="Menon",  specialization="Pediatrics",
               email="deepa@synthcare.com",  phone="8000000005"),
    ]
    db.add_all(doctors)
    db.commit()
    return {"message": f"Seeded {len(doctors)} doctors"}


@app.post("/seed/medicines")
def seed_medicines(db: Session = Depends(get_db)):
    medicines = [
        Medicine(name="Paracetamol 500mg",  generic_name="Paracetamol",  strength="500mg",
                 dosage_form="Tablet",  manufacturer="Sun Pharma",  unit_price=2.50),
        Medicine(name="Amoxicillin 250mg",  generic_name="Amoxicillin",  strength="250mg",
                 dosage_form="Capsule", manufacturer="Cipla",        unit_price=8.00),
        Medicine(name="Metformin 500mg",    generic_name="Metformin",    strength="500mg",
                 dosage_form="Tablet",  manufacturer="Dr. Reddy's",  unit_price=5.00),
        Medicine(name="Atorvastatin 10mg",  generic_name="Atorvastatin", strength="10mg",
                 dosage_form="Tablet",  manufacturer="Ranbaxy",      unit_price=12.00),
        Medicine(name="Omeprazole 20mg",    generic_name="Omeprazole",   strength="20mg",
                 dosage_form="Capsule", manufacturer="Zydus",        unit_price=6.50),
        Medicine(name="Cetirizine 10mg",    generic_name="Cetirizine",   strength="10mg",
                 dosage_form="Tablet",  manufacturer="Mankind",      unit_price=3.00),
        Medicine(name="Aspirin 75mg",       generic_name="Aspirin",      strength="75mg",
                 dosage_form="Tablet",  manufacturer="Bayer",        unit_price=1.50),
        Medicine(name="Azithromycin 500mg", generic_name="Azithromycin", strength="500mg",
                 dosage_form="Tablet",  manufacturer="Pfizer",       unit_price=15.00),
    ]
    db.add_all(medicines)
    db.flush()

    db.add_all([
        MedicineInventory(medicine_id=m.id, quantity=random.randint(5, 200), reorder_level=20)
        for m in medicines
    ])
    db.commit()
    return {"message": f"Seeded {len(medicines)} medicines with inventory"}


@app.post("/seed/appointments")
def seed_appointments(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    doctors  = db.query(Doctor).all()
    if not patients or not doctors:
        raise HTTPException(400, "Seed patients and doctors first")

    statuses = ["scheduled", "completed", "cancelled"]
    today    = date.today()
    appts    = []

    for i, patient in enumerate(patients):
        doctor = doctors[i % len(doctors)]
        appts.append(Appointment(
            patient_id       = patient.id,
            doctor_id        = doctor.id,
            appointment_date = datetime.combine(
                today + timedelta(days=i - 2), datetime.min.time()
            ).replace(hour=10 + i),
            status           = statuses[i % 3],
            notes            = f"Routine checkup for {patient.first_name}",
        ))

    db.add_all(appts)
    db.commit()
    return {"message": f"Seeded {len(appts)} appointments"}


@app.post("/seed/prescriptions")
def seed_prescriptions(db: Session = Depends(get_db)):
    patients     = db.query(Patient).all()
    doctors      = db.query(Doctor).all()
    medicines    = db.query(Medicine).all()
    appointments = db.query(Appointment).all()

    if not patients or not doctors or not medicines:
        raise HTTPException(400, "Seed patients, doctors, and medicines first")

    freq_map = {1: "Once daily", 2: "Twice daily", 3: "Thrice daily"}
    count = 0

    for i, patient in enumerate(patients[:3]):
        doctor = doctors[i % len(doctors)]
        appt   = appointments[i] if i < len(appointments) else None

        rx = Prescription(
            patient_id     = patient.id,
            doctor_id      = doctor.id,
            appointment_id = appt.id if appt else None,
        )
        db.add(rx)
        db.flush()

        for med in random.sample(medicines, 2):
            freq = random.choice([1, 2, 3])
            days = random.choice([5, 7, 10, 14])
            db.add(PrescriptionItem(
                prescription_id   = rx.id,
                medicine_id       = med.id,
                frequency_per_day = freq,
                frequency         = freq_map[freq],
                duration_days     = days,
                duration          = f"{days} days",
                dosage            = "1 tablet",
                instructions      = "Take after food",
            ))
        count += 1

    db.commit()
    return {"message": f"Seeded {count} prescriptions"}


@app.post("/seed/medical-records")
def seed_medical_records(db: Session = Depends(get_db)):
    patients     = db.query(Patient).all()
    doctors      = db.query(Doctor).all()
    appointments = db.query(Appointment).all()

    if not patients or not doctors:
        raise HTTPException(400, "Seed patients and doctors first")

    records_data = [
        ("Fever, headache",          "Viral fever",                "Rest, fluids, Paracetamol"),
        ("Chest pain, shortness",    "Hypertension",               "Atorvastatin, low sodium diet"),
        ("Fatigue, weight loss",     "Type 2 Diabetes",            "Metformin 500mg, diet control"),
        ("Joint pain, stiffness",    "Osteoarthritis",             "Physiotherapy, Aspirin"),
        ("Cough, cold, runny nose",  "Upper respiratory infection","Cetirizine, rest"),
    ]

    records = []
    for i, patient in enumerate(patients):
        symptoms, diagnosis, plan = records_data[i % len(records_data)]
        appt = appointments[i] if i < len(appointments) else None
        records.append(MedicalRecord(
            patient_id     = patient.id,
            doctor_id      = doctors[i % len(doctors)].id,
            appointment_id = appt.id if appt else None,
            symptoms       = symptoms,
            diagnosis      = diagnosis,
            treatment_plan = plan,
            notes          = f"Patient {patient.first_name} responded well to treatment.",
        ))

    db.add_all(records)
    db.commit()
    return {"message": f"Seeded {len(records)} medical records"}


@app.post("/seed/all")
def seed_all(db: Session = Depends(get_db)):
    _clear_all(db)
    seed_patients(db)
    seed_doctors(db)
    seed_medicines(db)
    seed_appointments(db)
    seed_prescriptions(db)
    seed_medical_records(db)
    return {
        "message": (
            "✅ All dummy data seeded: "
            "5 patients, 5 doctors, 8 medicines, "
            "5 appointments, 3 prescriptions, 5 medical records"
        )
    }

@app.get("/joins/prescription-details")
def prescription_details(prescription_id: int = None, patient_id: int = None, 
                         limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(
        Prescription.id.label("prescription_id"),
        Patient.first_name.label("patient_first_name"),
        Patient.last_name.label("patient_last_name"),
        Doctor.first_name.label("doctor_first_name"),
        Doctor.last_name.label("doctor_last_name"),
        Doctor.specialization,
        Medicine.id.label("medicine_id"),
        Medicine.name.label("medicine_name"),
        Medicine.generic_name,
        PrescriptionItem.dosage,
        PrescriptionItem.frequency,
        PrescriptionItem.frequency_per_day,
        PrescriptionItem.duration_days,
        PrescriptionItem.duration,
        PrescriptionItem.instructions,
        Prescription.created_at,
    ).join(Patient, Prescription.patient_id == Patient.id)\
     .join(Doctor,  Prescription.doctor_id  == Doctor.id)\
     .join(PrescriptionItem, PrescriptionItem.prescription_id == Prescription.id)\
     .join(Medicine, PrescriptionItem.medicine_id == Medicine.id)

    if prescription_id:
        q = q.filter(Prescription.id == prescription_id)
    if patient_id:
        q = q.filter(Prescription.patient_id == patient_id)

    return [dict(r._mapping) for r in q.limit(limit).all()]


from backend.rag_agent.brain import BrainConversationManager

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
def chat(req: ChatRequest):
    brain = BrainConversationManager()
    brain.history = req.history
    result = brain.chat(req.message)
    return {"answer": result["answer"], "plan": result.get("plan", {})}



class IndexQuestionRequest(BaseModel):
    document_id: str
    question: str

@app.post("/records/build-page-index")
def build_page_index(
    patient_id: int = Form(...),
    doctor_id: int = Form(None),
    record_type: str = Form("general_report"),
    file: UploadFile = File(...)
):
    try:
        # Pass the spooled file object and filename to keep FastAPI decoupled from logic
        result = process_and_index_pdf(
            file_obj=file.file,
            filename=file.filename,
            patient_id=patient_id,
            doctor_id=doctor_id,
            record_type=record_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@app.post("/records/ask-index")
def ask_indexed_pdf(req: IndexQuestionRequest):
    try:
        result = answer_pdf_question(
            document_id=req.document_id,
            question=req.question
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM synthesis failed: {str(e)}")