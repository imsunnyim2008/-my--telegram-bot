import os
import sqlite3
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from openai import AsyncOpenAI

load_dotenv()
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("companion")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-20b").strip()
DB_PATH = os.getenv("DATABASE_PATH", "companion.db")
BOT_NAME = os.getenv("BOT_NAME", "Nova")
DEFAULT_PERSONALITY = os.getenv(
    "BOT_PERSONALITY",
    "You are a warm, thoughtful, friendly Telegram AI companion. "
    "Be natural, respectful, supportive, and concise. Never claim to be human. "
    "Do not encourage dependency or tell users to avoid trusted people. "
    "If a user may be in immediate danger, encourage contacting local emergency services "
    "or a trusted person. Match the user's language and tone."
)
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "16"))
MAX_MESSAGE_CHARS = 4000

keyboard = ReplyKeyboardMarkup(
    [["💬 Chat", "🧠 My memory"], ["🎭 Personality", "🗑 Clear memory"], ["❔ Help"]],
    resize_keyboard=True,
)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                display_name TEXT,
                personality TEXT NOT NULL DEFAULT 'friendly',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def ensure_user(user_id: int, display_name: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO users(user_id, display_name, created_at) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET display_name=excluded.display_name",
            (user_id, display_name, datetime.now(timezone.utc).isoformat())
        )

def get_personality(user_id: int) -> str:
    with db() as conn:
        row = conn.execute("SELECT personality FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["personality"] if row else "friendly"

def set_personality(user_id: int, personality: str):
    with db() as conn:
        conn.execute("UPDATE users SET personality=? WHERE user_id=?", (personality, user_id))

def save_message(user_id: int, role: str, content: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO messages(user_id, role, content, created_at) VALUES(?,?,?,?)",
            (user_id, role, content[:MAX_MESSAGE_CHARS], datetime.now(timezone.utc).isoformat())
        )

def get_history(user_id: int):
    with db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, MAX_HISTORY_MESSAGES)
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def clear_history(user_id: int):
    with db() as conn:
        conn.execute("DELETE FROM messages WHERE user_id=?", (user_id,))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.full_name or "Telegram user")
    await update.message.reply_text(
        f"Hey {user.first_name or 'there'}! 👋 I'm {BOT_NAME}, your AI companion.\n\n"
        "We can talk, brainstorm, or just hang out. I can remember recent messages "
        "to keep the conversation flowing. Use /personality to change my style, "
        "or /clear to delete your chat memory.\n\n"
        "Your conversations are stored in this bot's database. Don't share passwords "
        "or sensitive information.",
        reply_markup=keyboard,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — Start chatting\n"
        "/help — Show commands\n"
        "/personality — Choose my conversation style\n"
        "/memory — See what memory is saved\n"
        "/clear — Delete your saved chat history\n"
        "/about — About this bot\n\n"
        "Or simply send me a message."
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{BOT_NAME} is a configurable AI companion bot. It uses Groq's AI API for replies "
        "and a local SQLite database for conversation history. The bot is not a human "
        "or a replacement for professional help."
    )

async def personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choices = "Choose a style with one of these commands:\n/personality friendly\n/personality funny\n/personality thoughtful\n/personality coach"
    if context.args:
        choice = " ".join(context.args).lower().strip()
        allowed = {"friendly", "funny", "thoughtful", "coach"}
        if choice not in allowed:
            await update.message.reply_text("Available styles: friendly, funny, thoughtful, coach.")
            return
        set_personality(update.effective_user.id, choice)
        await update.message.reply_text(f"🎭 Style updated to: {choice}.")
        return
    await update.message.reply_text(choices)

async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = get_history(update.effective_user.id)
    if not history:
        await update.message.reply_text("🧠 I don't have any saved conversation history for you yet.")
        return
    count = sum(1 for item in history if item["role"] == "user")
    await update.message.reply_text(
        f"🧠 I currently keep up to {MAX_HISTORY_MESSAGES} recent messages for conversation context. "
        f"There are {count} of your messages in the current history window. Use /clear to delete it."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_history(update.effective_user.id)
    await update.message.reply_text("🗑 Your saved conversation history has been deleted.")

def style_instruction(style: str) -> str:
    return {
        "friendly": "Be warm and friendly.",
        "funny": "Use light, good-natured humor when it fits; do not force jokes.",
        "thoughtful": "Be reflective, curious, and considerate.",
        "coach": "Be encouraging and practical; suggest clear next steps without being pushy.",
    }.get(style, "Be warm and friendly.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if not message or not message.text:
        return
    text_in = message.text.strip()
    if not text_in:
        return
    if text_in in ("💬 Chat", "🧠 My memory", "🎭 Personality", "🗑 Clear memory", "❔ Help"):
        actions = {
            "💬 Chat": "Send me anything you'd like to talk about.",
            "🧠 My memory": None,
            "🎭 Personality": None,
            "🗑 Clear memory": None,
            "❔ Help": None,
        }
        if text_in == "🧠 My memory":
            await memory(update, context)
        elif text_in == "🎭 Personality":
            await personality(update, context)
        elif text_in == "🗑 Clear memory":
            await clear(update, context)
        elif text_in == "❔ Help":
            await help_command(update, context)
        else:
            await message.reply_text(actions[text_in])
        return
    if not GROQ_API_KEY:
        await message.reply_text(
            "The bot is running, but AI replies aren't configured yet. Add GROQ_API_KEY "
            "to your environment variables, then restart the bot."
        )
        return
    ensure_user(user.id, user.full_name or "Telegram user")
    if len(text_in) > MAX_MESSAGE_CHARS:
        await message.reply_text(f"Please keep messages under {MAX_MESSAGE_CHARS} characters.")
        return
    await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
    save_message(user.id, "user", text_in)
    history = get_history(user.id)
    style = get_personality(user.id)
    client = AsyncOpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": f"{DEFAULT_PERSONALITY}\nBot name: {BOT_NAME}\nStyle: {style_instruction(style)}"},
                *history,
            ],
            temperature=0.8,
            max_tokens=600,
        )
        reply = (response.choices[0].message.content or "").strip()
        if not reply:
            reply = "I didn't come up with a reply that time. Try sending that again?"
        save_message(user.id, "assistant", reply)
        for i in range(0, len(reply), 4000):
            await message.reply_text(reply[i:i + 4000], reply_markup=keyboard)
    except Exception:
        log.exception("AI response failed")
        await message.reply_text(
            "Sorry, I couldn't get a reply from the AI service just now. Please try again shortly."
        )
    finally:
        await client.close()

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN. Set it in your .env or hosting environment.")
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("personality", personality))
    app.add_handler(CommandHandler("memory", memory))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    log.info("Starting %s Telegram companion bot", BOT_NAME)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
