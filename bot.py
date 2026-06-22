import asyncio
import logging
import os

import aiofiles
import aiohttp
import script
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "Токен бота не найден! Убедитесь, что создали файл .env и записали туда BOT_TOKEN."
    )

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

TRACKS_PER_PAGE = 7

class MusicStates(StatesGroup):
    searching = State()

def get_page_data(tracks: list, page: int):
    start_idx = page * TRACKS_PER_PAGE
    end_idx = start_idx + TRACKS_PER_PAGE
    page_tracks = tracks[start_idx:end_idx]

    total_pages = (len(tracks) + TRACKS_PER_PAGE - 1) // TRACKS_PER_PAGE

    message_text = f"<i>🔍 Страница {page + 1} из {total_pages}\n\n</i>"

    track_buttons = []
    for i, track in enumerate(page_tracks, start=start_idx + 1):
        title = f"{track['artist']} — {track['title']} ({track['duration']})"
        message_text += f"<b>{i}.</b> {title}\n\n"
        track_buttons.append(
            InlineKeyboardButton(text=str(i), callback_data=f"track_{i}")
        )

    keyboard_rows = [track_buttons]

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}")
        )
    if end_idx < len(tracks):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page + 1}")
        )

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    return message_text, keyboard


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        """<b>Boeing Music</b> ✈️

Помогу найти и скачать любой трек. Работаю быстро и без лишней рекламы.

<b>Как искать музыку:</b>
Просто отправь мне название песни или имя артиста в ответном сообщении.

<i><b>Пример:</b>
Navai — Чёрный мерен</i>

Отправь запрос, и я сразу выведу список треков 🛫""",
        parse_mode="html",
    )


@dp.message(F.text)
async def handle_music_request(message: types.Message, state: FSMContext):
    request = message.text
    print(f"=== БОТ ПОЛУЧИЛ ЗАПРОС: {request} ===")
    response = script.search(request) 
    print(f"=== РЕЗУЛЬТАТ ИЗ SCRIPT.PY: {response} ===")

    if not response:
        await message.answer("😕 Ничего не нашёл, попробуй другое название.")
        return

    await state.update_data(tracks=response, current_page=0)
    await state.set_state(MusicStates.searching)

    message_text, keyboard = get_page_data(response, page=0)

    await message.answer(
        message_text, parse_mode="html", reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("page_"), MusicStates.searching)
async def process_page_switch(callback: types.CallbackQuery, state: FSMContext):
    new_page = int(callback.data.split("_")[1])
    
    user_data = await state.get_data()
    tracks = user_data.get("tracks", [])

    if not tracks:
        await callback.answer("❌ Результаты поиска устарели. Введите запрос заново.")
        return

    await state.update_data(current_page=new_page)

    message_text, keyboard = get_page_data(tracks, page=new_page)

    try:
        await callback.message.edit_text(
            text=message_text,
            parse_mode="html",
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка обновления страницы: {e}")
        await callback.answer()


@dp.callback_query(F.data.startswith("track_"), MusicStates.searching)
async def send_track(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Загружаю трек...")

    index = int(callback.data.split("_")[1]) - 1

    user_data = await state.get_data()
    tracks = user_data.get("tracks", [])

    if index >= len(tracks) or index < 0:
        await callback.answer("❌ Ошибка: трек не найден в истории поиска.")
        return

    track = tracks[index]
    url = track["url"]

    if url.startswith("/"):
        url = f"https://eu.hitmoz.com{url}"

    raw_title = f"{track['artist']} — {track['title']}.mp3"
    clean_title = "".join(
        c for c in raw_title if c.isalnum() or c in "._- "
    ).strip()

    if len(clean_title) > 120:
        clean_title = clean_title[:116] + ".mp3"

    filename = os.path.join(TEMP_DIR, clean_title)

    try:
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await callback.message.answer(
                        "⚠️ Не удалось скачать трек (сервер музыки выдал ошибку)."
                    )
                    return

                async with aiofiles.open(filename, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 64):
                        await f.write(chunk)

        await callback.message.answer_audio(
            audio=types.FSInputFile(filename),
            caption="✈️ <b>Boeing Music</b> | Приятного прослушивания\n🔍 Найти ещё: @boeingmusicbot",
            parse_mode="html"
        )

    except Exception as e:
        await callback.message.answer("⚠️ Возникла ошибка при отправке трека.")
        logging.error(f"Ошибка при скачивании/отправке файла: {e}")

    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                logging.error(f"Не удалось удалить файл {filename}: {e}")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")