import os
import random
import asyncio
from datetime import datetime, timedelta

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from openai import AsyncOpenAI
import nest_asyncio


# 🔐 Ключи
TELEGRAM_TOKEN = "7918303095:AAHFdfT3PBQQxU5aOTLxIZXWTEUCHR_aEUo"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# 👥 Пользователи
chat_ids_str = os.getenv("CHAT_IDS", "")
chat_ids = [int(cid.strip()) for cid in chat_ids_str.split(",") if cid.strip().isdigit()]
if not chat_ids:
    chat_ids = [7034170724, 7602795208]

# 📅 Планировщик
scheduler = AsyncIOScheduler()
bot_instance: Bot = None

# 🎀 Генерация комплимента
async def generate_compliment():
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты генератор комплиментов для девушки по имени Азиза. Комплименты должны быть женственными, искренними, оригинальными и с эмодзи."},
            {"role": "user", "content": "Сгенерируй милый, оригинальный комплимент для Азизы"}
        ],
        max_tokens=200,
        temperature=0.9
    )
    return response.choices[0].message.content.strip()

# 📤 Отправка комплиментов
async def send_compliment():
    try:
        compliment = await generate_compliment()
        print(f"[💌] Комплимент: {compliment}")
        for uid in chat_ids:
            await bot_instance.send_message(chat_id=uid, text=compliment)
            print(f"[📤] Отправлен → {uid}")
    except Exception as e:
        print(f"[❌] Ошибка отправки: {e}")

# 🟢 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    username = update.effective_user.username or "без username"

    if user_id not in chat_ids:
        chat_ids.append(user_id)

    await update.message.reply_text("👋 Привет! Я с тобой — и с теплом 💖")
    print(f"[✅] /start от @{username} ({user_id})")

    run_time = datetime.now() + timedelta(minutes=1)
    scheduler.add_job(send_compliment, 'date', run_date=run_time)
    print(f"[⏳] Первый комплимент через 1 минуту в {run_time.strftime('%H:%M:%S')}")

# 🚀 Главный запуск
async def main():
    global bot_instance
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_instance = app.bot

    app.add_handler(CommandHandler("start", start))
    scheduler.start()

    # 📆 План 10 случайных комплиментов в день
    for _ in range(10):
        h = random.randint(9, 21)
        m = random.randint(0, 59)
        scheduler.add_job(send_compliment, 'cron', hour=h, minute=m)
        print(f"[🕒] Запланирован → {h:02}:{m:02}")

    print("🔥 Бот запущен! Напиши /start в Telegram.")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # ❗ Ждём бесконечно, чтобы бот не завершился
    await asyncio.Event().wait()

# ⚡ Точка входа
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
