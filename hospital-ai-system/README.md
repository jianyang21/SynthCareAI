# 🏥 Hospital AI System — Agentic Healthcare Platform

An end-to-end AI-powered hospital management system built with **CrewAI agents**, **RAG (Retrieval-Augmented Generation)**, and a **Telegram bot** for patient interaction. The system ingests patient EHR documents (PDFs), enables intelligent medical Q&A, appointment booking, medicine ordering, and emergency alerting — all through a conversational Telegram interface.

---

## 📐 System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        PATIENT INTERFACE                         │
│                                                                  │
│    ┌──────────────┐         ┌─────────────────────────────┐      │
│    │ Telegram Bot  │         │  REST API (FastAPI /docs)   │      │
│    │  (Polling)    │         │  POST /api/chat             │      │
│    └──────┬───────┘         │  POST /api/ingest           │      │
│           │                 │  GET/POST /api/appointments  │      │
│           │                 │  POST /api/medicine/order    │      │
│           │                 └──────────┬──────────────────┘      │
└───────────┼────────────────────────────┼─────────────────────────┘
            │                            │
            ▼                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                        AI ENGINE LAYER                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              Direct RAG + LLM Chat                      │     │
│  │  Free-text messages → Qdrant Search → LLM Response      │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              CrewAI Agent Orchestration                  │     │
│  │                                                         │     │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐  │     │
│  │  │ Medical   │ │Appointment│ │ Medicine  │ │Emergency│  │     │
│  │  │ QA Agent  │ │  Agent    │ │  Agent    │ │ Agent   │  │     │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └────┬───┘  │     │
│  │        │              │              │            │      │     │
│  │  ┌─────▼─────────────▼──────────────▼────────────▼───┐  │     │
│  │  │              CrewAI Tools Layer                    │  │     │
│  │  │  RAG Search │ DB Query │ Book Appt │ Order Meds │  │  │     │
│  │  │  Parse Rx   │ Emergency Alert (Telegram)         │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌───────────────────────────┐  ┌────────────────────────────┐   │
│  │     LLM Provider          │  │    RAG Pipeline             │   │
│  │  Ollama (Granite4) ←─┐    │  │  PDF → PyPDF → Chunks →    │   │
│  │  Gemini (Fallback) ←─┘    │  │  HuggingFace Embeddings →  │   │
│  │  Auto-switches based on   │  │  Qdrant Vector Store        │   │
│  │  Ollama availability      │  │  (+ PostgreSQL fallback)    │   │
│  └───────────────────────────┘  └────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
            │                            │
            ▼                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                     DATA & INFRASTRUCTURE                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  PostgreSQL   │  │    Qdrant     │  │       Redis          │   │
│  │  - Patients   │  │  - EHR Vector │  │  - Session Memory    │   │
│  │  - Appts      │  │    Embeddings │  │  - Short-term Chat   │   │
│  │  - Rx Orders  │  │  - Patient ID │  │    Context (20 msgs) │   │
│  │  - EHR Chunks │  │    Filtering  │  │                      │   │
│  │  - Memory     │  │              │  │                      │   │
│  │  (Fallback)   │  │              │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│       :5432              :6333              :6379                 │
│                     All via Docker Compose                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Orchestration & Workflow

### Patient Chat Flow
```
Patient sends message on Telegram
        │
        ▼
   ┌─────────────┐
   │ Telegram Bot │  ──→  Authorization Check
   └──────┬──────┘
          │
          ▼
   ┌──────────────────┐
   │  Direct RAG Chat  │  (for free-text messages)
   │                   │
   │  1. Embed query   │
   │  2. Search Qdrant │  ──→ Find relevant EHR chunks
   │  3. Build prompt  │      (filtered by patient_id)
   │  4. Call LLM      │  ──→ Ollama/Gemini
   │  5. Return answer │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │  Memory Module    │
   │  Save to Redis    │  (short-term: last 20 messages)
   │  Save to Postgres │  (long-term: permanent history)
   └──────────────────┘
```

### EHR Document Ingestion Flow
```
Admin uploads PDF via POST /api/ingest
        │
        ▼
   ┌─────────────┐
   │  PyPDFLoader │  ──→ Extract text from PDF
   └──────┬──────┘
          │
          ▼
   ┌───────────────────────────┐
   │  RecursiveCharacterSplitter│  ──→ 1000-char chunks, 200 overlap
   └──────────┬────────────────┘
              │
              ▼
   ┌────────────────────────┐
   │  HuggingFace Embeddings │  ──→ all-MiniLM-L6-v2 (384 dimensions)
   └──────────┬─────────────┘
              │
              ▼
   ┌──────────────────────────────────────────┐
   │  Qdrant Upsert                           │
   │  • Vector + payload (patient_id, content) │
   │  • Enables per-patient filtering          │
   ├──────────────────────────────────────────┤
   │  PostgreSQL Fallback                      │
   │  • Store chunks in document_chunks table  │
   │  • Used if Qdrant is unavailable          │
   └──────────────────────────────────────────┘
```

### Emergency Alert Flow
```
Patient sends /emergency or distress message
        │
        ▼
   ┌──────────────────┐
   │  Emergency Agent  │  ──→ Assess severity
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────────────────────────────────┐
   │  Telegram Alert Tool                          │
   │                                               │
   │  1. Send alert to HOSPITAL_TELEGRAM_ID        │
   │     "🚨 EMERGENCY: Patient X needs help"      │
   │                                               │
   │  2. Send alert to each emergency contact      │
   │     (friends/family from DB)                  │
   │                                               │
   │  3. Mark patient as critical in PostgreSQL    │
   └──────────────────────────────────────────────┘
```

### LLM Fallback Strategy
```
   ┌─────────────────┐
   │  Check: Is Ollama│
   │  running?        │
   └────┬────────┬────┘
        │ YES    │ NO
        ▼        ▼
   ┌────────┐ ┌──────────────┐
   │ Ollama │ │ Gemini 1.5   │
   │Granite4│ │ Flash (API)  │
   │ (Free) │ │ (Cloud)      │
   └────────┘ └──────────────┘
```

---

## 📁 Project Structure

```
hospital-ai-system/
├── app/
│   ├── main.py                  # FastAPI entrypoint + lifespan
│   ├── __init__.py
│   │
│   ├── agents/                  # CrewAI Agents
│   │   ├── crew.py              # Agent orchestrator (triage → specialist)
│   │   ├── direct_chat.py       # Direct RAG + LLM chat (no CrewAI overhead)
│   │   ├── triage_agent.py      # Intent classifier (5 categories)
│   │   ├── medical_qa.py        # Medical Q&A agent
│   │   ├── appointment_agent.py # Appointment scheduling
│   │   ├── medicine_agent.py    # Medicine ordering
│   │   └── emergency_agent.py   # Emergency detection & alerting
│   │
│   ├── tools/                   # CrewAI Tools (agent capabilities)
│   │   ├── rag_search.py        # Search patient EHR via RAG
│   │   ├── db_query.py          # Query patient info, Rx, appointments
│   │   ├── appointment_booking.py # Book/cancel appointments
│   │   ├── medicine_ordering.py # Order medicines, check status
│   │   ├── emergency_alert.py   # Send Telegram alerts to contacts
│   │   └── prescription_parser.py # Extract medicines from Rx docs
│   │
│   ├── rag/                     # RAG Pipeline
│   │   ├── embeddings.py        # HuggingFace embeddings singleton
│   │   ├── ingestion.py         # PDF → chunks → Qdrant + PostgreSQL
│   │   ├── retriever.py         # Search Qdrant (+ PG fallback)
│   │   └── qdrant_client.py     # Qdrant connection
│   │
│   ├── telegram/                # Telegram Bot
│   │   ├── bot.py               # Handlers, commands, polling
│   │   └── memory.py            # Dual-layer memory (Redis + PostgreSQL)
│   │
│   ├── api/                     # REST API
│   │   └── routes.py            # All HTTP endpoints
│   │
│   ├── config/
│   │   └── settings.py          # Pydantic settings (from .env)
│   │
│   ├── core/
│   │   ├── llm_provider.py      # LLM auto-fallback (Ollama → Gemini)
│   │   ├── celery_app.py        # Celery task queue
│   │   ├── redis_client.py      # Redis connection
│   │   └── logger.py            # Structured logging (structlog)
│   │
│   └── db/
│       ├── database.py          # SQLAlchemy async engine + session
│       └── models.py            # 8 ORM models (Patient, EHR, Rx, etc.)
│
├── docker-compose.yml           # PostgreSQL + Qdrant + Redis
├── pyproject.toml               # Python dependencies
├── .env.example                 # Template for environment variables
├── .gitignore                   # Protects secrets & data
├── create_sample_ehr.py         # Generate sample EHR PDF for testing
└── README.md                    # This file
```

---

## 🗄️ Database Schema

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   patients   │     │  prescriptions   │     │   appointments     │
├──────────────┤     ├──────────────────┤     ├────────────────────┤
│ id (PK)      │◄──┐ │ id (PK)          │     │ id (PK)            │
│ name         │   │ │ patient_id (FK)  │──►  │ patient_id (FK)    │
│ phone        │   │ │ doctor_name      │     │ doctor_name        │
│ telegram_id  │   │ │ diagnosis        │     │ department         │
│ emergency_   │   │ │ medications (JSON)│    │ appointment_date   │
│   contact    │   │ │ notes            │     │ reason             │
│ is_critical  │   │ │ prescribed_at    │     │ status             │
│ created_at   │   │ └──────────────────┘     └────────────────────┘
└──────────────┘   │
                   │ ┌──────────────────┐     ┌────────────────────┐
                   │ │  ehr_documents   │     │  document_chunks   │
                   │ ├──────────────────┤     ├────────────────────┤
                   ├─│ patient_id (FK)  │     │ document_id (FK)   │
                   │ │ filename         │──►  │ patient_id (FK)    │
                   │ │ chunk_count      │     │ content            │
                   │ │ uploaded_at      │     │ chunk_index        │
                   │ └──────────────────┘     │ qdrant_point_id    │
                   │                          └────────────────────┘
                   │ ┌──────────────────┐     ┌────────────────────┐
                   │ │ medicine_orders  │     │ emergency_contacts │
                   │ ├──────────────────┤     ├────────────────────┤
                   ├─│ patient_id (FK)  │     │ patient_id (FK)    │
                   │ │ medicines (JSON) │     │ name               │
                   │ │ total_price      │     │ phone              │
                   │ │ status           │     │ telegram_id        │
                   │ │ ordered_at       │     │ relationship_type  │
                   │ └──────────────────┘     └────────────────────┘
                   │
                   │ ┌────────────────────────┐
                   │ │ conversation_messages   │
                   │ ├────────────────────────┤
                   └─│ patient_id (FK)        │
                     │ role (user/assistant)   │
                     │ content                 │
                     │ created_at              │
                     └────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Required | Installation |
|------|----------|-------------|
| **Python 3.12+** | ✅ | [python.org](https://python.org) |
| **Docker Desktop** | ✅ | [docker.com](https://docker.com) |
| **Ollama** | ✅ | [ollama.com](https://ollama.com) |
| **Telegram Account** | ✅ | For bot interaction |

### Step 1: Clone & Setup

```bash
git clone https://github.com/jianyang21/SynthCareAI/blob/main/hospital-ai-system.git
cd hospital-ai-system

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -e .
pip install langchain-google-genai litellm pypdf reportlab
```

### Step 2: Configure Environment

```bash
# Copy the template
cp .env.example .env

# Edit .env with your values:
# - TELEGRAM_BOT_TOKEN  (from @BotFather on Telegram)
# - GEMINI_API_KEY       (from Google AI Studio, optional)
# - HOSPITAL_TELEGRAM_ID (your Telegram @username for alerts)
```

### Step 3: Start Infrastructure

```bash
# Start PostgreSQL, Qdrant, Redis
docker compose up -d

# Start Ollama + pull model
ollama serve                    # (if not already running)
ollama pull granite4:micro-h    # 1.9 GB
```

### Step 4: Start the Server

```bash
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

You should see:
```
database_tables_created
telegram_bot_polling_started
application_started
Uvicorn running on http://127.0.0.1:8000
```

### Step 5: Upload an EHR PDF

```bash
# Generate a sample EHR PDF
python create_sample_ehr.py

# Upload via API (PowerShell)
$form = @{ patient_id="1"; file = Get-Item sample_ehr_patient1.pdf }
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/ingest -Method Post -Form $form
```

Or use the **Swagger UI** at `http://127.0.0.1:8000/docs`

### Step 6: Chat on Telegram

1. Open your bot on Telegram
2. Send `/start` to register
3. Ask: *"What are my medications?"*
4. Try: `/my_info`, `/book_appointment`, `/order_medicine`

---

## 🤖 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register as a patient |
| `/my_info` | View full patient summary (from RAG + DB) |
| `/book_appointment` | Schedule a doctor visit |
| `/order_medicine` | Order medicines from prescriptions |
| `/emergency` | Trigger emergency alerts to hospital & contacts |
| *Free text* | Ask any health question — AI answers from your EHR |

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server status |
| `GET` | `/health` | Aggregate health check (DB, Redis, Qdrant) |
| `GET` | `/docs` | Swagger UI (interactive API docs) |
| `POST` | `/api/ingest` | Upload EHR PDF for a patient |
| `POST` | `/api/chat` | Chat with AI (same as Telegram) |
| `GET` | `/api/appointments/{id}` | List patient appointments |
| `POST` | `/api/appointments` | Book an appointment |
| `POST` | `/api/medicine/order` | Order medicines |

---

## 🧠 AI & LLM Configuration

### LLM Fallback Strategy

The system automatically selects the best available LLM:

| Priority | Provider | Model | When Used |
|----------|----------|-------|-----------|
| 1st | **Ollama** (local) | `granite4:micro-h` | When Ollama is running |
| 2nd | **Gemini** (cloud) | `gemini-1.5-flash` | When Ollama is unavailable |

Change the model in `.env`:
```
OLLAMA_MODEL=gemma3:4b    # Better quality, needs 4GB+ RAM
```

### Embedding Model

Uses `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) for vectorizing EHR documents. Runs locally — no API key needed.

---

## 🛡️ Security

| Feature | Implementation |
|---------|---------------|
| **Bot Access Control** | `ALLOWED_TELEGRAM_IDS` in `.env` — whitelist specific users |
| **Patient Data Isolation** | Qdrant filters by `patient_id` — patients only see their own records |
| **Local LLM** | Ollama keeps medical data off the cloud |
| **Secret Management** | All credentials in `.env`, excluded via `.gitignore` |
| **Auto-Registration** | Patients register via Telegram with their Telegram ID |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (async Python) |
| **AI Agents** | CrewAI + LiteLLM |
| **LLM** | Ollama (Granite4) / Google Gemini (fallback) |
| **RAG** | LangChain + Qdrant + HuggingFace Embeddings |
| **Database** | PostgreSQL (via SQLAlchemy async) |
| **Vector DB** | Qdrant |
| **Cache/Memory** | Redis |
| **Bot** | python-telegram-bot (polling mode) |
| **Task Queue** | Celery + Redis |
| **Logging** | structlog (JSON structured logs) |
| **Containers** | Docker Compose |

---

## � Future Roadmap

### Phase 3 — Medicine Booking Site Integration & Decrease the latency in the LLM Responses 
- [ ] Connect the Medicine Agent to the hospital's pharmacy website
- [ ] Browser automation (Playwright) or API integration for real-time ordering
- [ ] Live stock checking and price lookup from the pharmacy portal
- [ ] Order tracking and delivery status updates via Telegram
- [ ] Try to make the LLM Response more Faster

### Phase 4 — Advanced RAG System
- [ ] Hybrid search: **BM25 + Dense Embeddings** for better retrieval accuracy
- [ ] Cross-encoder **reranking** (ms-marco-MiniLM) to improve result relevance
- [ ] Improved chunking strategy — semantic chunking with section headers preserved
- [ ] Multi-modal EHR support (scanned images, handwritten notes via OCR)
- [ ] Query expansion and hypothetical document embeddings (HyDE)

### Phase 5 — Frontend Web Application
- [ ] Full-featured React/Next.js web dashboard as an upgrade from Telegram
- [ ] Patient portal: view records, appointments, prescriptions, lab trends
- [ ] Doctor dashboard: patient overview, alert management, notes
- [ ] Admin panel: user management, system monitoring, analytics
- [ ] Mobile-responsive PWA for on-the-go access

### Phase 6 — 24/7 Production Deployment
- [ ] Deploy agents as always-on services with auto-restart and monitoring
- [ ] Real-time appointment reminders and medication alerts via Telegram/push notifications
- [ ] Scheduled health check-ins and follow-up prompts
- [ ] Background tasks for periodic lab result analysis and anomaly detection
- [ ] Rate limiting, circuit breakers, and graceful degradation

### Phase 7 — Data Privacy & Compliance
- [ ] Full **HIPAA** compliance for patient data handling (US)
- [ ] **GDPR** compliance for EU patients — right to erasure, data portability
- [ ] **DISHA** (Digital Information Security in Healthcare Act) compliance for India
- [ ] End-to-end encryption for all patient communications
- [ ] Audit logging for all data access and modifications
- [ ] Consent management system — patients control their data sharing preferences
- [ ] Data anonymization pipeline for analytics and model training

### Phase 8 — Full Dockerization & Cloud Deployment
- [ ] Complete Docker Compose with all services (FastAPI, Celery, Ollama, Telegram bot)
- [ ] Multi-stage Dockerfile optimized for production (slim images)
- [ ] Kubernetes manifests for scalable cloud deployment (AWS/GCP/Azure)
- [ ] CI/CD pipeline with automated testing and deployment
- [ ] Health monitoring with Prometheus + Grafana dashboards
- [ ] Automated database backups and disaster recovery

### Phase 9 — Wearable Device Integration
- [ ] Support for **Fitbit**, **Apple Watch**, **Samsung Galaxy Watch** data ingestion
- [ ] Real-time vitals monitoring: heart rate, SpO2, blood pressure, sleep patterns
- [ ] Automated anomaly detection on wearable data (e.g., irregular heartbeat)
- [ ] Proactive health alerts: *"Your heart rate has been elevated for 2 hours"*
- [ ] Integration with Google Fit / Apple HealthKit APIs
- [ ] Wearable data visualization in the patient dashboard

---

## �📝 License

This project is for educational and research purposes. Consult a medical professional for actual health decisions.
