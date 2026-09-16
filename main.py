import asyncio
import json
import logging
import os
import html
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo
)

# QAYD: Telegram bot tokenlarini hech qachon ochiq kodda qoldirmang! 
# Token atrofidagi ortiqcha bo'shliqlarni olib tashlang.
BOT_TOKEN = "8275673607:AAH8_WLyYxk7MxYdC-x92qKSvq6tr46-DN0"
MOVIES_FILE = "movies.json"

# Sayt manzili (Telegram Web App uchun HTTPS bo'lishi shart)
APP_URL = "https://etvcinema.vercel.app"

def load_movies():
    if os.path.exists(MOVIES_FILE):
        with open(MOVIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Pastki menyudagi WebApp tugmasi
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🚀 Saytni ochish",
                web_app=WebAppInfo(url="https://etvcinema.vercel.app")
            )
        ]
    ],
    resize_keyboard=True
)

# Inline xabar ostidagi WebApp tugmasi
def get_webapp_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎬 Kinolarni ko'rish (Mini App)", 
                    web_app=WebAppInfo(url="https://etvcinema.vercel.app")
                )
            ]
        ]
    )

@dp.message(CommandStart())
async def start_handler(message: types.Message, command: CommandObject):
    movie_code = command.args  # Mini App'dan o'tilganda keladigan kod (masalan: /start 101)
    
    if movie_code:
        movies = load_movies()
        if movie_code in movies:
            movie = movies[movie_code]
            await message.answer_video(
                video=movie["file_id"],
                caption=movie["caption"],
                parse_mode="HTML"
            )
            return
        else:
            await message.answer("⚠️ <b>Bunday kodli kino topilmadi!</b> ❌", parse_mode="HTML")
            return

    user_name = html.escape(message.from_user.first_name)
    text = (
        f"👋 <b>Xush kelibsiz, {user_name}!</b>\n\n"
        f"🎬 Iltimos, kino kodini kiriting yoki Mini App orqali tanlang:"
    )
    await message.answer(
        text, 
        reply_markup=start_keyboard, 
        parse_mode="HTML"
    )

@dp.message(F.video)
async def catch_video_id(message: types.Message):
    caption_text = html.escape(message.caption or "🎬 Kino nomi ko'rsatilmagan")
    response_text = (
        f"📦 <b>Video ID olindi:</b>\n<code>{message.video.file_id}</code>\n\n"
        f"📌 <b>Tavsifi:</b>\n{caption_text}"
    )
    await message.answer(response_text, parse_mode="HTML")

@dp.message(F.text)
async def get_movie_by_code(message: types.Message):
    movie_code = message.text.strip()
    movies = load_movies()
    
    if movie_code in movies:
        movie = movies[movie_code]
        await message.answer_video(
            video=movie["file_id"],
            caption=movie["caption"],
            parse_mode="HTML"
        )
    else:
        await message.answer("⚠️ <b>Bunday kodli kino topilmadi!</b>\n\nIltimos, kodni to'g'ri kiriting ❌", parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())