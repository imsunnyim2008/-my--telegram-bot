import os
import logging
import sqlite3
from datetime import datetime, timezone

import telebot
from dotenv import load_dotenv
from google import genai

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("telegram_companion")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash").strip()
BOT_NAME = os.getenv("BOT_NAME", "Nova")
DATABASE_PATH = os.getenv("DATABASE_PATH", "companion.db")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "16"))
MAX_MESSAGE_CHARS = 4000

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN. Set it in your .env file or hosting environment.")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
ai = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def save_message(user_id, role, content):
    with connect_db() as conn:
        conn.execute(
            "INSERT INTO messages(user_id, role, content, created_at) VALUES(?,?,?,?)",
            (user_id, role, content[:MAX_MESSAGE_CHARS], datetime.now(timezone.utc).isoformat())
        )

def get_history(user_id):
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, MAX_HISTORY_MESSAGES)
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

def clear_history(user_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM messages WHERE user_id=?", (user_id,))

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        f"👋 Hey {message.from_user.first_name or 'there'}! I'm {BOT_NAME}, your AI companion.\n\n"
        "Send me a message to chat. Use /help for commands or /clear to erase your saved chat history. "
        "Please don't share passwords or sensitive information."
    )

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "/start — Start chatting\n"
        "/help — Show commands\n"
        "/about — About the bot\n"
        "/memory — Check saved chat history\n"
        "/clear — Delete your saved chat history"
    )

@bot.message_handler(commands=["about"])
def about(message):
    bot.reply_to(
        message,
        f"{BOT_NAME} is an AI companion powered by Google's Gemini API when an API key is configured. "
        "It is software, not a human or a replacement for professional help."
    )

@bot.message_handler(commands=["memory"])
def memory(message):
    history = get_history(message.from_user.id)
    user_count = sum(1 for item in history if item["role"] == "user")
    bot.reply_to(
        message,
        f"🧠 I keep up to {MAX_HISTORY_MESSAGES} recent messages for conversation context. "
        f"Your current history window contains {user_count} of your messages. Use /clear to erase it."
    )

@bot.message_handler(commands=["clear"])
def clear(message):
    clear_history(message.from_user.id)
    bot.reply_to(message, "🗑 Your saved conversation history has been deleted.")

@bot.message_handler(content_types=["text"])
def chat(message):
    text_in = (message.text or "").strip()
    if not text_in or text_in.startswith("/"):
        return
    if len(text_in) > MAX_MESSAGE_CHARS:
        bot.reply_to(message, f"Please keep messages under {MAX_MESSAGE_CHARS} characters.")
        return
    if ai is None:
        bot.reply_to(
            message,
            "AI replies aren't configured yet. Add GEMINI_API_KEY to your environment variables and restart the bot."
        )
        return

    user_id = message.from_user.id
    save_message(user_id, "user", text_in)
    history = get_history(user_id)
    try:
        bot.send_chat_action(message.chat.id, "typing")
        conversation = []
        for item in history:
            speaker = "User" if item["role"] == "user" else BOT_NAME
            conversation.append(f"{speaker}: {item['content']}")
        prompt = (
            f"You are {BOT_NAME}, a warm, thoughtful, friendly AI companion. "
            "Be natural, respectful, supportive, and concise. Never claim to be human. "
            "Do not encourage dependency or tell users to avoid trusted people. "
            "Match the user's language and tone.\n\n"
            "Continue this conversation using the recent history below. Respond only as the assistant.\n\n"
            + "\n".join(conversation)
            + f"\n{BOT_NAME}:"
        )
        response = ai.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
        )
        reply = (response.text or "").strip()
        if not reply:
            reply = "I couldn't come up with a reply just then. Please try again."
        save_message(user_id, "assistant", reply)
        for start_at in range(0, len(reply), 4000):
            bot.reply_to(message, reply[start_at:start_at + 4000])
    except Exception:
        log.exception("Gemini response failed")
        bot.reply_to(message, "Sorry, I couldn't get an AI reply right now. Please try again shortly.")

if __name__ == "__main__":
    init_db()
    log.info("Starting %s", BOT_NAME)
    bot.infinity_polling(skip_pending=True)
