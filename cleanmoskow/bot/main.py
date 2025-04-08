

import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cleanmoskow.settings")
django.setup()

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings

from handlers import start, waste, location, universal_handler

logging.basicConfig(level=logging.INFO)
TOKEN = settings.TELEGRAM_BOT_TOKEN

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    # dp.include_router(location.router)

    # dp.include_router(waste.router)
    # dp.include_router(game.router)
    dp.include_router(universal_handler.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())