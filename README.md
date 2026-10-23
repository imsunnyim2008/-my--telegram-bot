# Telegram AI Companion Bot

A Python Telegram bot that chats with users using Google's Gemini API. It includes basic commands and per-user conversation history stored in SQLite.

## Features

- `/start` — Start the bot
- `/help` — List commands
- `/about` — About the bot
- `/memory` — Show the recent history window
- `/clear` — Delete your saved conversation history
- AI conversation through Gemini
- Per-user SQLite chat history
- Configuration through environment variables (no secrets hard-coded)

## Requirements

- Python 3.10 or newer
- A Telegram bot token from Telegram's official `@BotFather`
- A Gemini API key from https://aistudio.google.com/apikey

Google AI Studio may offer free API usage with limits; model availability, regional eligibility, and quotas can change. Check the current terms and limits for your account.

## Setup on Windows

1. Install Python 3.10+.
2. Open this repository folder in VS Code or Command Prompt.
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to a new file named `.env`.
5. Open `.env` and add your own Telegram token and Gemini API key.
6. Run the bot:

   ```bash
   python Bot.py
   ```

Keep the terminal running while you want the bot online.

## Environment variables

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Secret token from @BotFather |
| `GEMINI_API_KEY` | Secret key used for AI responses |
| `AI_MODEL` | Optional model ID; defaults to `gemini-2.5-flash` |
| `BOT_NAME` | Optional display name; defaults to `Nova` |
| `DATABASE_PATH` | Optional SQLite path; defaults to `companion.db` |
| `MAX_HISTORY_MESSAGES` | Optional recent-message limit; defaults to `16` |

## Security and privacy

- Never commit your real `.env` file, Telegram token, or AI API key.
- The old version of this project contained a Telegram token in source code. Revoke that token in @BotFather and generate a new one. Removing it from the file does not make an exposed token safe again.
- This bot stores recent chat text in a local SQLite database. Explain this to users before inviting them to use the bot.
- Do not ask users for passwords, payment-card details, or other secrets.
- This bot is not a human, therapist, or emergency service.

## Deployment

Run it on a host that supports a continuously running Python worker. Add the environment variables in the host's secret/environment settings. Check current pricing, API quotas, and persistent-storage rules before choosing a host. A local SQLite file can be lost on hosts with temporary filesystems.

## Troubleshooting

- **Missing token:** Add `TELEGRAM_BOT_TOKEN` to `.env`.
- **AI not configured:** Add `GEMINI_API_KEY`.
- **AI API errors:** Check the API key, model ID, regional availability, and account quotas.
- **Bot stops replying:** Make sure the Python process is still running and the host supports long-running workers.
