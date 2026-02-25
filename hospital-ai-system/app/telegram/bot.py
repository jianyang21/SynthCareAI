"""
Telegram Bot — Patient-facing interface to the Hospital AI System.

Uses python-telegram-bot in POLLING mode (no ngrok/webhook needed).
"""
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from sqlalchemy import create_engine, text

from app.config.settings import settings
from app.core.logger import logger
from app.telegram.memory import save_message, get_chat_history_text
from app.agents.crew import classify_and_route

# Global application reference
telegram_app: Application = None


def _is_authorized(telegram_id: int) -> bool:
    """Check if a Telegram user is allowed to use the bot."""
    allowed = settings.ALLOWED_TELEGRAM_IDS.strip()
    if not allowed:
        return True  # empty = allow everyone (dev mode)
    allowed_ids = [x.strip() for x in allowed.split(",") if x.strip()]
    return str(telegram_id) in allowed_ids


def _get_sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    return create_engine(url)


def _get_patient_id_by_telegram(telegram_id: str) -> int | None:
    """Look up patient_id from telegram_id."""
    engine = _get_sync_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM patients WHERE telegram_id = :tid"),
            {"tid": str(telegram_id)},
        ).fetchone()
    return row[0] if row else None


def _register_patient(telegram_id: str, name: str) -> int:
    """Auto-register a new patient from Telegram."""
    engine = _get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "INSERT INTO patients (name, phone, telegram_id) "
                "VALUES (:name, :phone, :tid) RETURNING id"
            ),
            {"name": name, "phone": f"tg_{telegram_id}", "tid": str(telegram_id)},
        )
        conn.commit()
        return result.fetchone()[0]


# ──────────────────────  Command Handlers  ──────────────────────


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Access denied. You are not authorized to use this bot.")
        return
    patient_id = _get_patient_id_by_telegram(str(user.id))

    if not patient_id:
        patient_id = _register_patient(str(user.id), user.full_name)
        await update.message.reply_text(
            f"👋 Welcome to the Hospital AI Assistant, {user.first_name}!\n\n"
            f"You've been registered as Patient #{patient_id}.\n\n"
            f"I can help you with:\n"
            f"💬 Medical questions — just type your question\n"
            f"📅 /book_appointment — schedule a doctor visit\n"
            f"💊 /order_medicine — order your medicines\n"
            f"🚨 /emergency — report an emergency\n"
            f"📋 /my_info — view your patient info"
        )
    else:
        await update.message.reply_text(
            f"Welcome back, {user.first_name}! 👋\n"
            f"How can I help you today?\n\n"
            f"Just type your question or use a command."
        )


async def cmd_book_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /book_appointment command."""
    user = update.effective_user
    patient_id = _get_patient_id_by_telegram(str(user.id))
    if not patient_id:
        await update.message.reply_text("Please /start first to register.")
        return

    query = " ".join(context.args) if context.args else "I want to book an appointment with a doctor"
    await update.message.reply_text("📅 Looking into appointment options...")

    response = await asyncio.to_thread(classify_and_route, query, patient_id)
    save_message(patient_id, "user", query)
    save_message(patient_id, "assistant", response)
    await update.message.reply_text(response)


async def cmd_order_medicine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /order_medicine command."""
    user = update.effective_user
    patient_id = _get_patient_id_by_telegram(str(user.id))
    if not patient_id:
        await update.message.reply_text("Please /start first to register.")
        return

    query = " ".join(context.args) if context.args else "I want to order medicines from my prescription"
    await update.message.reply_text("💊 Checking your prescriptions...")

    response = await asyncio.to_thread(classify_and_route, query, patient_id)
    save_message(patient_id, "user", query)
    save_message(patient_id, "assistant", response)
    await update.message.reply_text(response)


async def cmd_emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /emergency command."""
    user = update.effective_user
    patient_id = _get_patient_id_by_telegram(str(user.id))
    if not patient_id:
        await update.message.reply_text("Please /start first to register.")
        return

    reason = " ".join(context.args) if context.args else "Patient triggered emergency alert via Telegram"
    await update.message.reply_text("🚨 Emergency alert being processed...")

    from app.agents.crew import run_emergency_check
    response = await asyncio.to_thread(run_emergency_check, reason, patient_id)
    save_message(patient_id, "user", f"EMERGENCY: {reason}")
    save_message(patient_id, "assistant", response)
    await update.message.reply_text(response)


async def cmd_my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_info command — shows full patient summary from DB + RAG."""
    user = update.effective_user
    patient_id = _get_patient_id_by_telegram(str(user.id))
    if not patient_id:
        await update.message.reply_text("Please /start first to register.")
        return

    await update.message.reply_text("📋 Fetching your records...")

    try:
        # 1. Get basic patient info from DB
        engine = _get_sync_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT name, phone, emergency_contact, is_critical FROM patients WHERE id = :pid"),
                {"pid": patient_id},
            ).fetchone()

        patient_name = row[0] if row else "Unknown"
        patient_phone = row[1] if row else "N/A"
        emergency_contact = row[2] if row and row[2] else "Not set"
        is_critical = row[3] if row else False

        # 2. Get EHR summary from RAG (all chunks for this patient)
        from app.rag.retriever import retrieve
        chunks = retrieve("patient complete medical record summary diagnoses prescriptions lab results", patient_id=patient_id, top_k=10)

        # 3. Format the response
        response_parts = [
            f"📋 *Patient Summary*\n",
            f"👤 Name: {patient_name}",
            f"📞 Phone: {patient_phone}",
            f"🏥 Emergency Contact: {emergency_contact}",
            f"⚠️ Critical: {'YES' if is_critical else 'No'}",
            f"🆔 Patient ID: {patient_id}",
        ]

        if chunks:
            response_parts.append(f"\n📄 *Medical Records ({len(chunks)} records found):*\n")
            for i, chunk in enumerate(chunks, 1):
                content = chunk["content"].strip()
                # Truncate very long chunks
                if len(content) > 500:
                    content = content[:500] + "..."
                response_parts.append(f"--- Record {i} ---\n{content}\n")
        else:
            response_parts.append("\n⚠️ No EHR documents uploaded yet. Ask the hospital to upload your records.")

        # 4. Get appointments from DB
        with engine.connect() as conn:
            appts = conn.execute(
                text("SELECT doctor_name, department, appointment_date, status FROM appointments WHERE patient_id = :pid ORDER BY appointment_date DESC LIMIT 3"),
                {"pid": patient_id},
            ).fetchall()

        if appts:
            response_parts.append("\n📅 *Recent Appointments:*")
            for a in appts:
                response_parts.append(f"  • Dr. {a[0]} ({a[1]}) — {a[2]} [{a[3]}]")
        else:
            response_parts.append("\n📅 No appointments scheduled.")

        full_response = "\n".join(response_parts)

        # Telegram has a 4096 char limit per message
        if len(full_response) > 4000:
            # Split into multiple messages
            await update.message.reply_text(full_response[:4000])
            await update.message.reply_text(full_response[4000:])
        else:
            await update.message.reply_text(full_response)

    except Exception as exc:
        logger.error("my_info_error", patient_id=patient_id, error=str(exc))
        await update.message.reply_text(f"❌ Error fetching records: {str(exc)[:200]}")



# ──────────────────────  Free-text Chat Handler  ──────────────────────


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-text messages — direct RAG + LLM chat (fast, no CrewAI overhead)."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Access denied. You are not authorized to use this bot.")
        return
    patient_id = _get_patient_id_by_telegram(str(user.id))
    if not patient_id:
        await update.message.reply_text(
            "Please send /start first to register with the hospital."
        )
        return

    message = update.message.text
    await update.message.reply_text("🤔 Thinking...")

    # Get conversation context
    chat_history = get_chat_history_text(patient_id, count=6)

    try:
        # Direct RAG + LLM chat (no CrewAI — faster and more reliable)
        from app.agents.direct_chat import direct_chat
        response = await asyncio.to_thread(
            direct_chat, message, patient_id, chat_history
        )
    except Exception as exc:
        error_msg = str(exc)
        logger.error("chat_error", patient_id=patient_id, error=error_msg)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            response = "⚠️ The AI service is temporarily rate-limited. Please wait a minute and try again."
        else:
            response = f"❌ Sorry, something went wrong. Please try again.\nError: {error_msg[:200]}"

    # Save to memory
    save_message(patient_id, "user", message)
    save_message(patient_id, "assistant", response)

    await update.message.reply_text(response)


# ──────────────────────  Bot Lifecycle  ──────────────────────


def create_bot_application() -> Application:
    """Build and configure the Telegram bot application."""
    global telegram_app

    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.warning("telegram_bot_token_not_set")
        return None

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("book_appointment", cmd_book_appointment))
    app.add_handler(CommandHandler("order_medicine", cmd_order_medicine))
    app.add_handler(CommandHandler("emergency", cmd_emergency))
    app.add_handler(CommandHandler("my_info", cmd_my_info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    telegram_app = app
    logger.info("telegram_bot_configured")
    return app


async def start_polling():
    """Start the bot in polling mode (for local development)."""
    app = create_bot_application()
    if app is None:
        logger.warning("telegram_bot_not_started_no_token")
        return

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info("telegram_bot_polling_started")


async def stop_polling():
    """Stop the bot polling."""
    global telegram_app
    if telegram_app and telegram_app.updater.running:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("telegram_bot_stopped")
