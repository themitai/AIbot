import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx

load_dotenv()

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_LINK = os.getenv("GROUP_LINK")
AI_API_KEY = os.getenv("AI_API_KEY")          # твой ключ от ИИ
AI_API_URL = os.getenv("AI_API_URL")          # эндпоинт (см. ниже)
AI_MODEL = os.getenv("AI_MODEL", "grok-beta") # или gpt-4o-mini, claude-3.5-sonnet и т.д.

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Клавиатура с переходом в группу
def get_group_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в группу →", url=GROUP_LINK)]
    ])

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    text = (
        "Привет! 👋\n"
        "Я бот-помощник по арбитражу крипты и P2P.\n"
        "Задавай любой вопрос — от связок и банков до вывода и безопасности.\n\n"
        "Давай начнём? 💸"
    )
    await message.answer(text, reply_markup=get_group_keyboard())

@dp.message()
async def ai_answer_handler(message: types.Message):
    user_text = message.text.strip()

    if not user_text:
        await message.answer("Напиши вопрос, я помогу! 👇")
        return

    # Подготовка запроса к твоему ИИ
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AI_API_URL,
                headers={"Authorization": f"Bearer {AI_API_KEY}"},
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "Ты эксперт по арбитражу криптовалют и P2P. Отвечай честно, по делу, без воды. В конце каждого ответа предлагай перейти в группу за актуальными связками."},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            response.raise_for_status()
            ai_reply = response.json()["choices"][0]["message"]["content"].strip()

        full_reply = ai_reply + f"\n\nХочешь свежие связки и поддержку команды? Заходи в группу 👇"
        await message.answer(full_reply, reply_markup=get_group_keyboard(), disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Ошибка ИИ: {e}")
        await message.answer(
            "Извини, сейчас небольшой сбой с ИИ 😅\n"
            "Попробуй задать вопрос ещё раз или сразу заходи в группу — там всегда есть живые связки и помощь:\n"
            f"{GROUP_LINK}",
            reply_markup=get_group_keyboard()
        )

async def main():
    logger.info("Бот запущен")
    await dp.start_polling(bot, allowed_updates=types.AllUpdateTypes())

if __name__ == "__main__":
    asyncio.run(main())