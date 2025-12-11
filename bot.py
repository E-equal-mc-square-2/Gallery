import os
import json
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import aiohttp
from aiohttp import web
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8544594534:AAGQj54F5PzscVlP64RNVNyOfnNdHwDzy5M"
AUTHORIZED_CHAT_ID = 2140020900

PUBLIC_DIR = "public"
GALLERY_JSON = os.path.join(PUBLIC_DIR, "gallery.json")
LATEST_JPG = os.path.join(PUBLIC_DIR, "latest.jpg")
LATEST_TXT = os.path.join(PUBLIC_DIR, "latest.txt")

os.makedirs(PUBLIC_DIR, exist_ok=True)

if not os.path.exists(GALLERY_JSON):
    with open(GALLERY_JSON, "w") as f:
        json.dump([], f)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

upload_mode = {}

def get_next_photo_number():
    with open(GALLERY_JSON, "r") as f:
        gallery = json.load(f)
    return len(gallery) + 1

def update_gallery(photo_name):
    with open(GALLERY_JSON, "r") as f:
        gallery = json.load(f)
    gallery.append(photo_name)
    with open(GALLERY_JSON, "w") as f:
        json.dump(gallery, f, indent=2)

def save_latest(photo_path):
    with open(LATEST_TXT, "w") as f:
        f.write(datetime.utcnow().isoformat() + "Z")

def get_gallery():
    with open(GALLERY_JSON, "r") as f:
        return json.load(f)

def delete_photo(photo_id):
    gallery = get_gallery()
    if 1 <= photo_id <= len(gallery):
        to_delete = gallery[photo_id - 1]
        del gallery[photo_id - 1]
        os.remove(os.path.join(PUBLIC_DIR, to_delete))
        with open(GALLERY_JSON, "w") as f:
            json.dump(gallery, f, indent=2)
        if gallery:
            latest = gallery[-1]
            os.replace(os.path.join(PUBLIC_DIR, latest), LATEST_JPG)
            save_latest(LATEST_JPG)
        elif os.path.exists(LATEST_JPG):
            os.remove(LATEST_JPG)
        return True
    return False

@router.message(Command("upload"))
async def cmd_upload(message: Message):
    if message.chat.id != AUTHORIZED_CHAT_ID:
        return
    if "gallery" in message.text:
        upload_mode[message.chat.id] = True
        await message.reply("Send me the photo to upload to the gallery.")
    else:
        await message.reply("Usage: /upload gallery")

@router.message(Command("list"))
async def cmd_list(message: Message):
    if message.chat.id != AUTHORIZED_CHAT_ID:
        return
    if "gallery" in message.text:
        gallery = get_gallery()
        if not gallery:
            await message.reply("Gallery is empty.")
        else:
            txt = "\n".join([f"{i+1}. {name}" for i, name in enumerate(gallery)])
            await message.reply(f"Gallery photos:\n{txt}")
    else:
        await message.reply("Usage: /list gallery")

@router.message(Command("delete"))
async def cmd_delete(message: Message):
    if message.chat.id != AUTHORIZED_CHAT_ID:
        return
    parts = message.text.split()
    if len(parts) == 3 and parts[1] == "gallery":
        try:
            photo_id = int(parts[2])
            if delete_photo(photo_id):
                await message.reply(f"Photo #{photo_id} deleted.")
            else:
                await message.reply("Invalid photo ID.")
        except ValueError:
            await message.reply("Invalid photo ID.")
    else:
        await message.reply("Usage: /delete gallery [id]")

@router.message(F.photo)
async def handle_photo(message: Message):
    if message.chat.id != AUTHORIZED_CHAT_ID:
        return
    if upload_mode.get(message.chat.id, False):
        upload_mode[message.chat.id] = False
        photo_id = get_next_photo_number()
        file_name = f"photo{photo_id}.jpg"
        file_path = os.path.join(PUBLIC_DIR, file_name)
        file = await bot.get_file(message.photo[-1].file_id)
        await bot.download_file(file.file_path, file_path)
        update_gallery(file_name)
        if os.path.exists(LATEST_JPG):
            os.remove(LATEST_JPG)
        os.link(file_path, LATEST_JPG)
        save_latest(LATEST_JPG)
        await message.reply(f"Photo #{photo_id} uploaded bro, shrine slayed 😈🔥")
    else:
        await message.reply("Send /upload gallery first.")

dp.include_router(router)

async def static_handler(request):
    path = request.match_info.get('path', 'index.html')
    if path == '':
        path = 'index.html'
    file_path = os.path.join(PUBLIC_DIR, path)
    if not os.path.exists(file_path):
        raise web.HTTPNotFound()
    return web.FileResponse(file_path)

async def start_webserver():
    app = web.Application()
    app.router.add_route('GET', '/{path:.*}', static_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main():
    await start_webserver()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
