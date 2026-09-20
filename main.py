import asyncio
import json
import logging
import os
import html
from pathlib import Path
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8275673607:AAF2mIba2Hu1V4gckWixHZLPT96aTK2DxC0")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN Railway Variables bo'limida berilishi kerak")

ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Telegram ID-ingizni kiriting
MOVIES_FILE = Path(__file__).resolve().parent / "movies.json"
APP_URL = "https://etvcinema.vercel.app"

movies_cache = {}

def load_movies():
    """Kinolarni fayldan xavfsiz o'qib olish va keshga saqlash"""
    global movies_cache
    if os.path.exists(MOVIES_FILE):
        try:
            with open(MOVIES_FILE, "r", encoding="utf-8") as f:
                movies_cache = json.load(f)
                logging.info(f"✅ {len(movies_cache)} ta kino keshga yuklandi.")
        except Exception as e:
            logging.error(f"❌ JSON faylni o'qishda xatolik: {e}")
            movies_cache = {}
    else:
        logging.warning(f"⚠️ {MOVIES_FILE} fayli topilmadi!")
        movies_cache = {}
    return movies_cache

# Bot obyektida default parse_mode ni HTML ga sozlaymiz
bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🚀 Saytni ochish",
                web_app=WebAppInfo(url=APP_URL)
            )
        ]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start_handler(message: types.Message, command: CommandObject):
    movie_code = command.args
    
    if movie_code:
        movie = movies_cache.get(movie_code)
        if movie:
            caption = movie.get("caption", "")
            await message.answer_video(
                video=movie["file_id"],
                caption=caption
            )
            return
        else:
            await message.answer("⚠️ <b>Bunday kodli kino topilmadi!</b> ❌")
            return

    user_name = html.escape(message.from_user.first_name)
    text = (
        f"👋 <b>Xush kelibsiz, {user_name}!</b>\n\n"
        f"🎬 Iltimos, kino kodini kiriting yoki Mini App orqali tanlang:"
    )
    await message.answer(
        text, 
        reply_markup=start_keyboard
    )

@dp.message(Command("reload"))
async def reload_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    load_movies()
    await message.answer("🔄 <b>Kinolar ro'yxati qayta yuklandi!</b>")

@dp.message(F.video)
async def catch_video_id(message: types.Message):
    raw_caption = message.caption or "🎬 Kino nomi ko'rsatilmagan"
    safe_caption = html.escape(raw_caption)
    
    response_text = (
        f"📦 <b>Video ID olindi:</b>\n<code>{message.video.file_id}</code>\n\n"
        f"📌 <b>Tavsifi:</b>\n{safe_caption}"
    )
    await message.answer(response_text)

@dp.message(F.text)
async def get_movie_by_code(message: types.Message):
    # Saytni ochish tugmasini e'tiborsiz qoldirish
    if message.text == "🚀 Saytni ochish":
        return

    # Noma'lum buyruqlar kelganida
    if message.text.startswith("/"):
        await message.answer("⚠️ <b>Noma'lum buyruq!</b>\nKino ko'rish uchun faqat kodini yuboring.")
        return

    movie_code = message.text.strip()
    movie = movies_cache.get(movie_code)
    
    if movie:
        caption = movie.get("caption", "")
        await message.answer_video(
            video=movie["file_id"],
            caption=caption
        )
    else:
        await message.answer("⚠️ <b>Bunday kodli kino topilmadi!</b>\n\nIltimos, kodni to'g'ri kiriting ❌")


async def health_check(reader, writer):
    """Railway health check uchun yengil HTTP endpoint."""
    try:
        await reader.read(1024)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "Content-Length: 2\r\n"
            "Connection: close\r\n\r\n"
            "OK"
        )
        writer.write(response.encode("ascii"))
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    logging.basicConfig(level=logging.INFO)
    load_movies()

    port = int(os.getenv("PORT", "8080"))
    health_server = await asyncio.start_server(health_check, "0.0.0.0", port)
    logging.info("Health server %s portida ishga tushdi", port)

    try:
        await dp.start_polling(bot)
    finally:
        health_server.close()
        await health_server.wait_closed()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())