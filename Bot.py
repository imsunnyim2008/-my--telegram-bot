import telebot

# Insert your actual token here (but keep it private!)
bot = telebot.TeleBot("8003447410:AAFPjsC5ryjjQiaWeTkoQdFWiEWBUlu_KEM")

@bot.message_handler(func=lambda message: True)
def reply(message):
    text = message.text.lower()

    if "hi" in text or "hello" in text:
        bot.reply_to(message, "👋 Hey! I’m your personal bot.")
    elif "help" in text:
        bot.reply_to(message, "You can ask me anything. Type 'commands' to see more.")
    elif "commands" in text:
        bot.reply_to(message, "/start - Welcome\n/help - Help message\n/sayhi - Say Hi\n/hack - Fake hacker stuff 🤖")
    elif "/hack" in text:
        bot.reply_to(message, "🛠️ Initializing hack mode...\nAccess denied 😅 Just kidding!")
    else:
        bot.reply_to(message, f"You said: {message.text}")

bot.polling()
