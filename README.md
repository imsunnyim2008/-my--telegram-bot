# Telegram AI Companion Bot

A Python Telegram bot that chats with users using Groq's OpenAI-compatible API. It includes basic commands and per-user conversation history stored in SQLite.

## Features

- `/start` — Start the bot
- `/help` — List commands
- `/about` — About the bot
- `/memory` — Show the recent history window
- `/clear` — Delete your saved conversation history
- AI conversation through Groq
- Per-user SQLite chat history
- Configuration through environment variables (no secrets hard-coded)

## Requirements

- Python 3.10 or newer
- A Telegram bot token from Telegram's official `@BotFather`
- A Groq API key from https://console.groq.com/keys

Groq has a free tier with rate limits; model availability and limits can change.

## Setup on Windows

1. Install Python 3.10+.
2. Open this repository folder in VS Code or Command Prompt.
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to a new file named `.env`.
5. Open `.env` and add your own Telegram token and Groq API key.
6. Run the bot:

   ```bash
   python Bot.py
   ```

Keep the terminal running while you want the bot online.

## Environment variables

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Secret token from @BotFather |
| `GROQ_API_KEY` | Secret key used for AI responses |
| `AI_MODEL` | Optional model ID; defaults to `openai/gpt-oss-20b` |
| `BOT_NAME` | Optional display name; defaults to `Nova` |
| `DATABASE_PATH` | Optional SQLite path; defaults to `companion.db` |
| `MAX_HISTORY_MESSAGES` | Optional recent-message limit; defaults to `16` |

## Security and privacy

- Never commit your real `.env` file, Telegram token, or AI API key.
- If a token has ever been committed publicly, revoke it in @BotFather and generate a new one immediately. Removing it from the current file does not make an exposed token safe again.
- This bot stores recent chat text in a local SQLite database. Explain this to users before inviting them to use the bot.
- Do not ask users for passwords, payment-card details, or other secrets.
- This bot is not a human, therapist, or emergency service.

## Deployment

Run it on a host that supports a continuously running Python worker. Add the environment variables in the host's secret/environment settings. Check current pricing, free-tier limits, and persistent-storage rules before choosing a host. A local SQLite file can be lost on hosts with temporary filesystems.

## Troubleshooting

- **Missing token:** Add `TELEGRAM_BOT_TOKEN` to `.env`.
- **AI not configured:** Add `GROQ_API_KEY`.
- **AI API errors:** Check the API key, model ID, account limits, and logs.
- **Bot stops replying:** Make sure the Python process is still running and the host supports long-running workers.
