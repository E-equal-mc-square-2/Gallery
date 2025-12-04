import asyncio
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = 2140020900
PUBLIC_DIR = Path("public")
STATIC_DIR = Path("static")
GALLERY_JSON = PUBLIC_DIR / "gallery.json"
LATEST_TXT = PUBLIC_DIR / "latest.txt"
LATEST_JPG = PUBLIC_DIR / "latest.jpg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

user_states: Dict[int, Optional[str]] = {}

def ensure_directories():
    PUBLIC_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)
    if not GALLERY_JSON.exists():
        with open(GALLERY_JSON, "w") as f:
            json.dump([], f)
    if not LATEST_TXT.exists():
        with open(LATEST_TXT, "w") as f:
            f.write("")

def load_gallery():
    try:
        with open(GALLERY_JSON, "r") as f:
            return json.load(f)
    except:
        return []

def save_gallery(gallery):
    with open(GALLERY_JSON, "w") as f:
        json.dump(gallery, f, indent=2)

def get_next_photo_number():
    gallery = load_gallery()
    if not gallery:
        return 1
    numbers = []
    for photo in gallery:
        try:
            num = int(photo.replace("photo", "").replace(".jpg", ""))
            numbers.append(num)
        except:
            pass
    return max(numbers) + 1 if numbers else 1

def update_latest(photo_path):
    if photo_path.exists():
        shutil.copy(photo_path, LATEST_JPG)
        with open(LATEST_TXT, "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def is_owner(user_id: Optional[int]) -> bool:
    return user_id == OWNER_ID

@router.message(CommandStart())
async def cmd_start(message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        await message.answer("Access denied.")
        return
    await message.answer(
        "Welcome to Kilometres' Collection Bot!\n\n"
        "Commands:\n"
        "/upload gallery - Upload a photo to the gallery\n"
        "/list gallery - List all photos\n"
        "/delete gallery [id] - Delete a photo by ID"
    )

@router.message(Command("upload"))
async def cmd_upload(message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        await message.answer("Access denied.")
        return
    
    if not message.text:
        await message.answer("Usage: /upload gallery")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or args[1].lower() != "gallery":
        await message.answer("Usage: /upload gallery")
        return
    
    user_states[message.from_user.id] = "awaiting_photo"
    await message.answer("Send the photo now. It will be added to the gallery.")

@router.message(Command("list"))
async def cmd_list(message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        await message.answer("Access denied.")
        return
    
    if not message.text:
        await message.answer("Usage: /list gallery")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or args[1].lower() != "gallery":
        await message.answer("Usage: /list gallery")
        return
    
    gallery = load_gallery()
    if not gallery:
        await message.answer("Gallery is empty.")
        return
    
    lines = []
    for i, photo in enumerate(gallery, 1):
        num = photo.replace("photo", "").replace(".jpg", "")
        lines.append(f"{i}. Photo #{num}")
    
    await message.answer("Gallery Photos:\n" + "\n".join(lines))

@router.message(Command("delete"))
async def cmd_delete(message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        await message.answer("Access denied.")
        return
    
    if not message.text:
        await message.answer("Usage: /delete gallery [id]")
        return
    
    args = message.text.split()
    if len(args) < 3 or args[1].lower() != "gallery":
        await message.answer("Usage: /delete gallery [id]")
        return
    
    try:
        photo_id = int(args[2])
    except ValueError:
        await message.answer("Invalid photo ID. Use a number.")
        return
    
    gallery = load_gallery()
    photo_name = f"photo{photo_id}.jpg"
    
    if photo_name not in gallery:
        await message.answer(f"Photo #{photo_id} not found in gallery.")
        return
    
    photo_path = PUBLIC_DIR / photo_name
    if photo_path.exists():
        photo_path.unlink()
    
    gallery.remove(photo_name)
    save_gallery(gallery)
    
    if gallery:
        last_photo = gallery[-1]
        last_photo_path = PUBLIC_DIR / last_photo
        update_latest(last_photo_path)
    else:
        if LATEST_JPG.exists():
            LATEST_JPG.unlink()
        with open(LATEST_TXT, "w") as f:
            f.write("")
    
    await message.answer(f"Photo #{photo_id} deleted from gallery.")

@router.message(F.photo)
async def handle_photo(message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        await message.answer("Access denied.")
        return
    
    if user_states.get(message.from_user.id) != "awaiting_photo":
        await message.answer("Use /upload gallery first to enable photo upload mode.")
        return
    
    user_states[message.from_user.id] = None
    
    if not message.photo:
        await message.answer("No photo received.")
        return
    
    photo = message.photo[-1]
    photo_number = get_next_photo_number()
    photo_name = f"photo{photo_number}.jpg"
    photo_path = PUBLIC_DIR / photo_name
    
    file = await bot.get_file(photo.file_id)
    if not file.file_path:
        await message.answer("Failed to get photo file path.")
        return
    
    await bot.download_file(file.file_path, photo_path)
    
    gallery = load_gallery()
    gallery.append(photo_name)
    save_gallery(gallery)
    
    update_latest(photo_path)
    
    await message.answer(f"Photo #{photo_number} uploaded bro, shrine slayed 😈🔥")

async def handle_index(request):
    return web.FileResponse("static/index.html")

async def handle_static(request):
    filename = request.match_info.get("filename", "")
    file_path = STATIC_DIR / filename
    if file_path.exists():
        return web.FileResponse(file_path)
    return web.Response(status=404, text="Not Found")

async def handle_public(request):
    filename = request.match_info.get("filename", "")
    file_path = PUBLIC_DIR / filename
    if file_path.exists():
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*"
        }
        return web.FileResponse(file_path, headers=headers)
    return web.Response(status=404, text="Not Found")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/static/{filename:.*}", handle_static)
    app.router.add_get("/public/{filename:.*}", handle_public)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 5000)
    await site.start()
    print("Web server started on http://0.0.0.0:5000")

async def main():
    ensure_directories()
    print("Directories initialized")
    print(f"Owner ID: {OWNER_ID}")
    print("Starting bot and web server...")
    
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
