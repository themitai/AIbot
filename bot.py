import asyncio
import logging
import os
from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import httpx

load_dotenv()

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_LINK = os.getenv("GROUP_LINK")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_URL = os.getenv("AI_API_URL")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопка перехода в группу
def get_group_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в группу →", url=GROUP_LINK)]
    ])

@dp.message(CommandStart())
async def start_handler(message: Message):
    text = (
        "Привет! 👋\n"
        "Я бот-помощник по арбитражу крипты и P2P.\n"
        "Задавай любой вопрос — от связок и банков до вывода и безопасности.\n\n"
        "Давай начнём? 💸"
    )
    await message.answer(text, reply_markup=get_group_keyboard())

@dp.message()
async def ai_answer_handler(message: Message):
    user_text = message.text.strip()
    if not user_text:
        await message.answer("Напиши вопрос, я помогу! 👇")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AI_API_URL,
                headers={"Authorization": f"Bearer {AI_API_KEY}"},
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты эксперт по арбитражу криптовалют и P2P. Отвечай честно, по делу, без воды. В конце каждого ответа предлагай перейти в группу за актуальными связками и поддержкой команды."
                        },
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 600
                },
                timeout=35.0
            )
            response.raise_for_status()
            ai_reply = response.json()["choices"][0]["message"]["content"].strip()

        full_reply = ai_reply + f"\n\nХочешь свежие связки и поддержку команды? Заходи в группу 👇"
        await message.answer(full_reply, reply_markup=get_group_keyboard(), disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Ошибка ИИ: {e}")
        await message.answer(
            "Извини, сейчас небольшой сбой с ИИ 😅\n"
            "Попробуй задать вопрос ещё раз или сразу заходи в группу:\n"
            f"{GROUP_LINK}",
            reply_markup=get_group_keyboard()
        )

# ===================== WEBHOOK ДЛЯ RAILWAY =====================
async def on_startup(dispatcher: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)
    webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

async def on_shutdown(dispatcher: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удалён")

async def main():
    # Удаляем старый webhook
    await bot.delete_webhook(drop_pending_updates=True)

    # Устанавливаем новый
    webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

    # Запуск polling как запасной вариант (на Railway webhook предпочтительнее)
    # await dp.start_polling(bot)

# Запуск на Railway через aiohttp
app = web.Application()
webhook_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)
webhook_handler.register(app, path="/webhook")
setup_application(app, dp, bot=bot)

async def startup(app: web.Application):
    await on_startup(dp)

async def shutdown(app: web.Application):
    await on_shutdown(dp)

app.on_startup.append(startup)
app.on_shutdown.append(shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
