# Telegram AI Companion Bot

A beginner-friendly Telegram companion bot written in Python. Features include AI chat, per-user conversation history, personality styles, keyboard shortcuts, and a command to erase saved history.

## Features

- `/start`, `/help`, `/about`
- AI conversation powered by the OpenAI API
- Separate conversation history for each Telegram user
- `/personality friendly|funny|thoughtful|coach`
- `/memory` to inspect memory status
- `/clear` to erase saved conversation messages
- SQLite storage
- Environment variables for secrets and settings

## Requirements

- Python 3.10+
- A Telegram bot token from Telegram's official `@BotFather`
- An OpenAI API key for AI replies. API usage may cost money; ChatGPT subscriptions do not automatically include API credits.

## Run locally

1. Create a bot using `@BotFather` in Telegram and copy its token.
2. Copy `.env.example` to `.env`.
3. Put your Telegram token and OpenAI API key in `.env`.
4. Install dependencies:

   ```bash
   python -m venv .venv
   # Windows:
   .venv\\Scripts\\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. Start the bot:

   ```bash
   python main.py
   ```

## Deploy

Use a Python worker/background service on a host that supports long-running processes. Set the same environment variables in the host dashboard and run `python main.py`. Check the host's current pricing and persistent-disk/database rules before deploying; free hosting availability and limits can change. SQLite data may be lost on hosts with ephemeral filesystems.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Token from @BotFather |
| `OPENAI_API_KEY` | For AI replies | API key; keep secret |
| `AI_MODEL` | No | Defaults to `gpt-4o-mini` |
| `BOT_NAME` | No | Defaults to `Nova` |
| `BOT_PERSONALITY` | No | Base system instructions |
| `MAX_HISTORY_MESSAGES` | No | Recent message context window |
| `DATABASE_PATH` | No | SQLite database file path |

## Security and privacy

- Never commit your real `.env` file or tokens to GitHub.
- Anyone with your Telegram bot token can control your bot; regenerate it with @BotFather if exposed.
- This starter stores conversation text in SQLite. Tell users what is stored and who operates the bot before inviting the public.
- Do not collect passwords, payment card details, or other secrets.
- This bot is not a human, therapist, or emergency service.
- Add authentication and authorization before adding any admin-only commands.

## Customization

Edit `BOT_NAME`, `BOT_PERSONALITY`, and `style_instruction()` in `main.py`. You can add commands by defining an async handler and registering it in `main()`.

## Troubleshooting

- **Missing token:** set `TELEGRAM_BOT_TOKEN` in your environment.
- **AI not configured:** set `OPENAI_API_KEY`.
- **Invalid token:** check the token with @BotFather and replace it in your host settings.
- **AI errors:** check API billing/limits and the server logs.
