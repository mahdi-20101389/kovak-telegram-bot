import logging
import httpx
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

try:
    with open("persona.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "تو یک دستیار هوشمند هستی."

MAX_HISTORY_MESSAGES = 5
user_histories = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_history(chat_id: int):
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_histories[chat_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من دستیار هوش مصنوعی تو هستم. هر سوالی داری بپرس.")

async def reset_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text("🧹 حافظه پاک شد.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text
    history = get_history(chat_id)
    
    history.append({"role": "user", "content": user_message})

    if len(history) > (MAX_HISTORY_MESSAGES + 1):
        user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}]
        history = user_histories[chat_id]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"model": MODEL, "messages": history}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            reply = data['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": reply})
            await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_conversation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
