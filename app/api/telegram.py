import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from app.database import get_db
from app.api.chat import chat, ChatRequest

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives a Telegram message and runs it through the agent."""

    # Ignore non-text messages
    if not update.message or not update.message.text:
        return

    user_message = update.message.text
    # Use Telegram chat ID as session_id — unique per user, persistent across messages
    session_id = str(update.message.chat_id)

    # Send typing indicator while agent is thinking
    await update.message.chat.send_action("typing")

    try:
        # Reuse the exact same chat() function from chat.py
        db = next(get_db())
        try:
            request = ChatRequest(session_id=session_id, message=user_message)
            response = chat(request, db)
            await update.message.reply_text(response.response)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error handling Telegram message: {e}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again."
        )


def build_telegram_app() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app