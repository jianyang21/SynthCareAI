# SynthCare AI — Healthcare Agent

A healthcare management system powered by LangGraph ReAct agent + FastAPI + Streamlit.

## Project Structure

```
synthcare/
├── backend/
│   ├── __init__.py
│   ├── app.py          # FastAPI backend (database + REST API)
│   └── agent.py        # LangGraph agent with tools
├── frontend/
│   └── app.py          # Streamlit chat UI
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your values:
#   OPENAI_API_KEY=sk-...
#   DATABASE_URL=postgresql://user:password@localhost:5432/synthcare
#   BASE_URL=http://localhost:8000
```

### 3. Create the database

```bash
psql -U postgres -c "CREATE DATABASE synthcare;"
psql -U postgres -c "CREATE USER abhinav WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE synthcare TO abhinav;"
```

### 4. Start the FastAPI backend

```bash
# From the synthcare/ directory
uvicorn backend.app:app --reload --port 8000
```

The backend will auto-create all tables on startup.

### 5. Start the Streamlit frontend

```bash
# From the synthcare/ directory (important — run from project root)
streamlit run frontend/app.py
```

## Usage

Open `http://localhost:8501` in your browser.

### Example queries

- "Show me the dashboard analytics"
- "List all patients"
- "Create a patient named John Doe, male, email john@example.com, phone 9876543210, city Hyderabad, blood group O+"
- "Show all appointments with doctor details"
- "Which medicines are running low on stock?"
- "Generate order for prescription 1"
- "How many patients and doctors do we have?"

## Architecture

```
User Input
    │
    ▼
Streamlit UI (frontend/app.py)
    │  maintains ConversationManager instance in session_state
    ▼
ConversationManager (backend/agent.py)
    │  builds full message history: System + History + New Message
    ▼
LangGraph ReAct Agent (gpt-4o-mini)
    │  decides which tools to call
    ▼
LangChain Tools
    │  each tool calls FastAPI via HTTP
    ▼
FastAPI Backend (backend/app.py)
    │  executes queries/mutations
    ▼
PostgreSQL Database
```

## Key Fixes Over Original Code

| Issue | Fix |
|-------|-----|
| `/query` and `/create` used wrong request shape | Both now use Pydantic `BaseModel` with `table` + `filters`/`data` in body |
| Tool args were dicts, caused LangChain type errors | All tool args are now `str` (JSON strings), parsed inside the tool |
| Executor loop broke multi-step reasoning | Single agent call with full plan as one message |
| `.get()` deprecated in SQLAlchemy 2.x | Replaced with `.filter().first()` |
| No conversation history | `ConversationManager` accumulates full history and passes it each turn |
| Streamlit session state lost manager | Manager stored in `st.session_state` |