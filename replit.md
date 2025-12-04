# Kilometres' Collection - Telegram Photo Gallery

## Overview
A Telegram bot-powered photo gallery system featuring:
- Async Telegram bot (aiogram) for photo uploads
- Aiohttp web server for hosting the gallery
- Wet-dark neon purple/violet aesthetic UI
- Real-time auto-refreshing latest photo display
- Mobile-responsive infinite-scroll gallery

## Project Structure
```
/
├── bot.py              # Main backend: Telegram bot + aiohttp web server
├── static/
│   ├── index.html      # Gallery frontend
│   ├── styles.css      # Wet-dark neon theme
│   └── script.js       # Auto-refresh & lightbox functionality
├── public/             # Photo storage (auto-created)
│   ├── photo1.jpg      # Uploaded photos
│   ├── photo2.jpg
│   ├── latest.jpg      # Most recent photo copy
│   ├── latest.txt      # Timestamp of latest upload
│   └── gallery.json    # Array of all photo filenames
├── requirements.txt
└── replit.md
```

## Bot Commands (Owner Only - Chat ID: 2140020900)
- `/start` - Welcome message and command list
- `/upload gallery` - Enable photo upload mode, send next photo
- `/list gallery` - List all photos with numbers
- `/delete gallery [id]` - Delete specific photo by number

## Technical Details
- **Bot Token**: Stored as BOT_TOKEN environment variable
- **Web Server**: aiohttp on port 5000
- **Auto-refresh**: Latest photo refreshes every 2 seconds
- **Gallery refresh**: Every 3 seconds
- **Cache Control**: Disabled for real-time updates

## Recent Changes
- December 2024: Initial creation with full feature set

## User Preferences
- Clean, aesthetic UI with neon purple theme
- Mobile-first responsive design
- Real-time updates without page reload
