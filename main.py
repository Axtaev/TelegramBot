import os
import random
import asyncio
from datetime import datetime, timedelta

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from openai import AsyncOpenAI
import nest_asyncio

from dotenv import load_dotenv

load_dotenv()


# 🔐 Ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
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
    prompt_variants = [
    "Представь, что ты пишешь Азизе последнее письмо перед вечностью — сделай его незабываемым.",
    "Опиши, как будто Азиза — это само вдохновение. Только не банально, а возвышенно, метафорично и глубоко.",
    "Сделай комплимент Азизе в стиле древнегреческого поэта, чтобы даже боги Афродиты ревновали.",
    "Если бы ты мог сказать Азизе одну фразу, которая останется с ней на всю жизнь — что бы это было?",
    "Вообрази, что ты художник, а Азиза — твоя муза. Опиши её словами так, будто пишешь картину словом.",
    "Ты словно влюблённый философ эпохи Возрождения — скажи Азизе комплимент, от которого затрепещет душа.",
    "Азиза — твоя вселенная. Расскажи о ней так, будто ты наблюдаешь её через телескоп души.",
]


    prompt = random.choice(prompt_variants)

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "system",
            "content": (
                "Ты влюблённый поэт, философ и романтик, который пишет от чистого сердца "
                "исключительно для своей единственной — девушки по имени Азиза. "
                "Твоя задача — создавать **уникальные**, **душевные**, **поэтические** комплименты, признания и строки, "
                "будто ты вдохновлён её светом. Никакой банальщины, клише или повторов. "
                "Каждая строка — это как произведение искусства. Используй красивые образы, метафоры, эмоции и эмодзи 🌙💖✨. "
                "Говори так, как будто это последние слова любви на земле."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=250,
        temperature=1.2
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
    for _ in range(7):
        h = random.randint(0, 23)   # от 0 до 23 часов
        m = random.randint(0, 59)   # от 0 до 59 минут
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
