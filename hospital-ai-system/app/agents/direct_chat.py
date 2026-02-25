"""
Direct RAG-powered chat — bypasses CrewAI for faster, more reliable responses.

Uses the LLM directly with RAG context for answering questions.
Falls back to CrewAI only for specific actions (booking, ordering, emergency).
"""
from app.core.llm_provider import get_llm
from app.rag.retriever import get_context_text
from app.core.logger import logger


def direct_chat(message: str, patient_id: int, chat_history: str = "") -> str:
    """
    Answer a patient question directly using RAG + LLM.
    No CrewAI overhead — fast and reliable even with small models.
    """
    logger.info("direct_chat_start", patient_id=patient_id, message=message[:80])

    # 1. Retrieve relevant EHR context from Qdrant
    ehr_context = get_context_text(message, patient_id=patient_id, top_k=5)

    # 2. Build the prompt
    system_prompt = (
        "You are a helpful hospital AI assistant. You have access to the patient's "
        "electronic health records (EHR). Answer their question accurately and "
        "empathetically based on the medical records provided below.\n\n"
        "If the records don't contain relevant information, say so honestly. "
        "Always recommend consulting a doctor for serious concerns.\n"
        "Keep your response concise and clear."
    )

    context_block = f"--- Patient Medical Records ---\n{ehr_context}\n---" if ehr_context else "No medical records found for this patient."

    history_block = f"Recent conversation:\n{chat_history}\n" if chat_history else ""

    full_prompt = (
        f"{system_prompt}\n\n"
        f"{context_block}\n\n"
        f"{history_block}"
        f"Patient's question: {message}\n\n"
        f"Your response:"
    )

    # 3. Call LLM directly (no CrewAI)
    llm = get_llm(temperature=0.3)
    try:
        # Use litellm's completion directly for simplicity
        from litellm import completion

        # Determine model string
        from app.config.settings import settings
        import httpx
        try:
            httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
            model = f"ollama/{settings.OLLAMA_MODEL}"
        except Exception:
            model = f"gemini/gemini-1.5-flash"

        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_block}\n\n{history_block}Patient's question: {message}"},
            ],
            temperature=0.3,
            api_base=settings.OLLAMA_BASE_URL if "ollama" in model else None,
            api_key=settings.GEMINI_API_KEY if "gemini" in model else None,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("direct_chat_llm_error", error=str(exc))
        # Fallback: just return the RAG context if LLM fails
        if ehr_context:
            answer = f"I found these records for you:\n\n{ehr_context[:1500]}"
        else:
            answer = "I couldn't process your question right now. Please try again."

    logger.info("direct_chat_done", patient_id=patient_id)
    return answer
