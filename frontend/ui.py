"""
SynthCare AI — Streamlit Frontend
Run from the project root: streamlit run frontend/app.py
"""

import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import requests
import streamlit as st
from backend.rag_agent.brain import BrainConversationManager   # ← was ConversationManager from agent.py

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="SynthCare AI",
    page_icon="🏥",
    layout="wide",
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #1a73e8; }
    .sub-header  { color: #666; font-size: 0.95rem; margin-bottom: 1.5rem; }
    .tool-badge  {
        display: inline-block; background: #e8f0fe; color: #1a73e8;
        border-radius: 12px; padding: 2px 10px; font-size: 0.8rem;
        margin: 2px; font-family: monospace;
    }
    .delete-badge {
        display: inline-block; background: #fce8e6; color: #c5221f;
        border-radius: 12px; padding: 2px 10px; font-size: 0.8rem;
        margin: 2px; font-family: monospace;
    }
    .update-badge {
        display: inline-block; background: #e6f4ea; color: #137333;
        border-radius: 12px; padding: 2px 10px; font-size: 0.8rem;
        margin: 2px; font-family: monospace;
    }
    .plan-step {
        background: #f8f9fa; border-left: 3px solid #1a73e8;
        padding: 4px 10px; margin: 3px 0; border-radius: 0 6px 6px 0;
        font-size: 0.85rem; color: #333;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE
# ==========================================

if "manager" not in st.session_state:
    st.session_state.manager = BrainConversationManager()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown("## 🏥 SynthCare AI")
    st.markdown("---")

    st.markdown("### ⚙️ Settings")
    st.session_state.debug_mode = st.toggle(
        "Show plan + tool calls", value=st.session_state.debug_mode
    )

    st.markdown("---")

    # ── Seed dummy data ──────────────────────────────────────────────
    st.markdown("### 🌱 Test Data")
    backend_url = os.getenv("BASE_URL", "http://localhost:8000")

    if st.button("🏥 Seed all dummy data", use_container_width=True):
        with st.spinner("Seeding…"):
            try:
                r = requests.post(f"{backend_url}/seed/all", timeout=30)
                if r.status_code == 200:
                    st.success(r.json().get("message", "Seeded!"))
                else:
                    st.error(f"Seed failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 Patients", use_container_width=True):
            with st.spinner():
                r = requests.post(f"{backend_url}/seed/patients", timeout=10)
                st.success("Patients seeded!") if r.status_code == 200 else st.error(r.text)
        if st.button("💊 Medicines", use_container_width=True):
            with st.spinner():
                r = requests.post(f"{backend_url}/seed/medicines", timeout=10)
                st.success("Medicines seeded!") if r.status_code == 200 else st.error(r.text)
        if st.button("📋 Prescriptions", use_container_width=True):
            with st.spinner():
                r = requests.post(f"{backend_url}/seed/prescriptions", timeout=10)
                st.success("Prescriptions seeded!") if r.status_code == 200 else st.error(r.text)

    with col2:
        if st.button("🩺 Doctors", use_container_width=True):
            with st.spinner():
                r = requests.post(f"{backend_url}/seed/doctors", timeout=10)
                st.success("Doctors seeded!") if r.status_code == 200 else st.error(r.text)
        if st.button("📅 Appointments", use_container_width=True):
            with st.spinner():
                r = requests.post(f"{backend_url}/seed/appointments", timeout=10)
                st.success("Appointments seeded!") if r.status_code == 200 else st.error(r.text)
        if st.button("🗑️ Clear ALL data", use_container_width=True):
            with st.spinner():
                r = requests.post(f"{backend_url}/seed/clear", timeout=10)
                st.warning("All data cleared!") if r.status_code == 200 else st.error(r.text)

    st.markdown("---")
    st.markdown("### 💡 Example queries")

    examples = [
        "Show dashboard analytics",
        "List all patients",
        "List all doctors",
        "Show patient appointments",
        "Which medicines are low stock?",
        "What is Abhinav's hemoglobin?",
        "Search blood pressure for patient Priya",
        "Create a patient: Jane Smith, female, jane@example.com, 9876543210, Mumbai, B+",
        "Create a doctor: Ravi Kumar, specialization Cardiology",
        "Update doctor Abhinav's specialization to Neurology",
        "Update appointment 1 status to completed",
        "Delete doctor with id 2",
        "Generate order for prescription 1",
        "Show patient orders",
    ]

    for eq in examples:
        if st.button(eq, use_container_width=True, key=f"ex_{hash(eq)}"):
            st.session_state.pending_input = eq

    st.markdown("---")

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.manager = BrainConversationManager()
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Backend URL**")
    backend_url_input = st.text_input(
        "Backend URL",
        value=os.getenv("BASE_URL", "http://localhost:8000"),
        label_visibility="collapsed"
    )
    os.environ["BASE_URL"] = backend_url_input

    try:
        r = requests.get(f"{backend_url_input}/health", timeout=3)
        st.success("✅ Backend connected") if r.status_code == 200 else st.error("❌ Backend error")
    except Exception:
        st.error("❌ Backend unreachable")


# ==========================================
# TOOL BADGE HELPER
# ==========================================

def render_tool_badge(tool_name: str) -> str:
    if "delete" in tool_name:
        return f'<span class="delete-badge">🗑 {tool_name}</span>'
    elif "update" in tool_name:
        return f'<span class="update-badge">✏️ {tool_name}</span>'
    else:
        return f'<span class="tool-badge">🔧 {tool_name}</span>'


# ==========================================
# CHAT DISPLAY
# ==========================================

st.markdown('<div class="main-header">🏥 SynthCare AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Create, view, update, and delete patients, doctors, appointments, pharmacy records and more.</div>', unsafe_allow_html=True)

for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"]):
        st.write(entry["content"])

        if entry["role"] == "assistant" and st.session_state.debug_mode:

            # Show planner steps
            if entry.get("plan"):
                steps = entry["plan"].get("steps", [])
                if steps:
                    with st.expander(f"🗺️ Plan ({len(steps)} steps)", expanded=False):
                        for i, s in enumerate(steps):
                            st.markdown(f'<div class="plan-step">Step {i+1}: {s}</div>', unsafe_allow_html=True)

            # Show tool calls
            if entry.get("tool_calls"):
                with st.expander(f"🔧 Tools called ({len(entry['tool_calls'])})", expanded=False):
                    for tc in entry["tool_calls"]:
                        st.markdown(render_tool_badge(tc["tool"]), unsafe_allow_html=True)
                        if tc.get("args"):
                            st.json(tc["args"])


# ==========================================
# INPUT
# ==========================================

pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("Ask anything — create, update, delete, or query records...") or pending

if user_input:

    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.chat_history.append({
        "role": "user", "content": user_input, "tool_calls": [], "plan": None
    })

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            result = st.session_state.manager.chat(user_input)

        answer   = result["answer"]
        plan     = result.get("plan", {})
        tool_calls = []

        # Extract tool calls from execution results for display
        for step_text in result.get("execution", []):
            # tool call info lives in the brain's executor messages,
            # we surface them via the step result text for now
            pass

        st.write(answer)

        if st.session_state.debug_mode:
            steps = plan.get("steps", [])
            if steps:
                with st.expander(f"🗺️ Plan ({len(steps)} steps)", expanded=True):
                    for i, s in enumerate(steps):
                        st.markdown(f'<div class="plan-step">Step {i+1}: {s}</div>', unsafe_allow_html=True)

            execution = result.get("execution", [])
            if execution:
                with st.expander("📋 Execution trace", expanded=False):
                    for step_result in execution:
                        st.text(step_result)

        if result.get("error"):
            st.error("⚠️ Agent error — check if backend is running.")

    st.session_state.chat_history.append({
        "role":       "assistant",
        "content":    answer,
        "tool_calls": tool_calls,
        "plan":       plan,
    })