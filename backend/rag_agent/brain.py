"""
SynthCare Brain
Multi-step reasoning pipeline with shared context between steps and conversation memory.
Planner → Executor (with memory) → Validator
"""

import json
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from backend.rag_agent.agent import TOOLS, SYSTEM_PROMPT


# =========================================================
# MODELS
# =========================================================

planner_llm  = ChatOpenAI(model="gpt-4o-mini", temperature=0)
executor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
validator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# =========================================================
# EXECUTOR AGENT
# =========================================================

executor_agent = create_react_agent(executor_llm, TOOLS)


# =========================================================
# PLANNER
# =========================================================

def planner(user_input: str, conversation_history: List[Dict]) -> Dict[str, List[str]]:
    """
    Break user request into minimal, logical steps.
    Conversation history is injected so the planner understands
    references like "his", "that patient", "the same doctor", etc.
    """

    # Summarise recent turns so the planner has context without a huge prompt
    history_text = ""
    for msg in conversation_history[-6:]:          # last 3 turns (user + assistant each)
        role = msg["role"].upper()
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are a healthcare workflow planner.

Break the user request into minimal, logical steps that a tool-calling agent can execute one by one.

STRICT RULES:
- If a patient name is mentioned  → FIRST step must be: find patient_id using query_records
- If medical/health data needed   → MUST include a step: search_medical_records
- If CRUD operation               → use correct verb (create / update / delete)
- Each step must be self-contained and reference concrete values where known
- Do NOT skip steps
- Use the conversation history to resolve pronouns like "his", "her", "that patient"

Return ONLY valid JSON with no markdown fences:
{{
  "steps": [
    "step 1 description",
    "step 2 description"
  ]
}}

--- CONVERSATION HISTORY ---
{history_text if history_text else "(none)"}
----------------------------

User request:
{user_input}
"""

    try:
        res = planner_llm.invoke(prompt)
        content = res.content.strip().strip("```json").strip("```").strip()
        plan = json.loads(content)
        if "steps" not in plan or not plan["steps"]:
            raise ValueError("Empty plan")
        return plan
    except Exception:
        return {"steps": [user_input]}   # safe fallback: treat as single step


# =========================================================
# EXECUTOR  (THE KEY FIX — shared message thread)
# =========================================================

def executor(plan: Dict[str, List[str]], conversation_history: List[Dict]) -> List[str]:
    """
    Execute each step using the ReAct agent.

    KEY DESIGN:
    - A single `messages` list is built once and GROWS across steps.
    - Step N can see every tool call and result from Steps 1…N-1.
    - This is how patient_id (or any value) discovered in Step 1
      is automatically available in Step 2, 3, etc.
    - The system prompt and conversation history are always prepended
      so the agent knows the domain rules and prior turns.
    """

    # ── 1. Base messages: system prompt + recent conversation history ──
    messages: List = [SystemMessage(content=SYSTEM_PROMPT)]

    for msg in conversation_history[-10:]:         # last 5 turns
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    # ── 2. Execute each step, accumulating results into the same thread ──
    step_results: List[str] = []

    for i, step in enumerate(plan.get("steps", [])):

        step_text = str(step)

        # Tell the agent what step we are on and what came before
        prior_context = ""
        if step_results:
            prior_context = (
                "\n\nResults from previous steps (use these — do NOT re-fetch unless necessary):\n"
                + "\n".join(step_results)
                + "\n"
            )

        full_step_message = (
            f"[Step {i+1} of {len(plan['steps'])}]\n"
            f"{prior_context}"
            f"Now execute: {step_text}"
        )

        messages.append(HumanMessage(content=full_step_message))

        try:
            res = executor_agent.invoke({"messages": messages})

            # The agent may have added several messages (tool calls + results).
            # Append ALL new messages so the next step sees the full trace.
            new_messages = res["messages"][len(messages):]
            messages.extend(new_messages)

            output = res["messages"][-1].content
            if not isinstance(output, str):
                output = str(output)

            step_results.append(f"Step {i+1} ({step_text}):\n{output}")

        except Exception as e:
            error_msg = f"Step {i+1} ERROR: {str(e)}"
            messages.append(AIMessage(content=error_msg))
            step_results.append(error_msg)

    return step_results


# =========================================================
# VALIDATOR
# =========================================================

def validator(user_input: str, execution_results: List[str]) -> str:
    """
    Produce the final user-facing answer using ONLY tool outputs.
    Never hallucinates — if data is missing it says so.
    """

    combined = "\n\n".join(execution_results)

    prompt = f"""
You are a healthcare assistant producing a final answer for the user.

Use ONLY the tool results provided below.

STRICT RULES:
- Do NOT invent or assume any data not present in the results
- If a value is missing → say "No data found"
- Highlight key medical values clearly (Hb, BP, glucose, etc.)
- For CRUD confirmations → state exactly what was created / updated / deleted
- Be concise but complete

User request:
{user_input}

Tool results:
{combined}

Final Answer:
"""

    try:
        res = validator_llm.invoke(prompt)
        return res.content.strip()
    except Exception as e:
        return f"Error generating final answer: {str(e)}"


# =========================================================
# CONVERSATION MANAGER
# =========================================================

class BrainConversationManager:
    """
    Wraps the full Planner → Executor → Validator pipeline
    with persistent multi-turn conversation history.

    Usage:
        brain = BrainConversationManager()
        result = brain.chat("What is Abhinav's hemoglobin?")
        result = brain.chat("Now update his appointment to next Monday")
                                          ↑ "his" resolved via history
    """

    MAX_HISTORY = 20   # keep last 20 messages (10 turns)

    def __init__(self):
        self.history: List[Dict] = []

    def reset(self):
        self.history = []

    def chat(self, user_input: str) -> Dict[str, Any]:

        recent_history = self.history[-self.MAX_HISTORY:]

        # ── 1. Plan ──────────────────────────────────────────────────────
        plan = planner(user_input, recent_history)

        # ── 2. Execute ───────────────────────────────────────────────────
        execution_results = executor(plan, recent_history)

        # ── 3. Validate / Final Answer ───────────────────────────────────
        final_answer = validator(user_input, execution_results)

        # ── 4. Save to history ───────────────────────────────────────────
        self.history.append({"role": "user",      "content": user_input})
        self.history.append({"role": "assistant", "content": final_answer})

        return {
            "plan":      plan,
            "execution": execution_results,
            "answer":    final_answer,
            "error":     False,
        }