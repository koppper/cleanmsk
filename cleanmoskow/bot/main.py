

import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cleanmoskow.settings")
django.setup()

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import start, waste, location

logging.basicConfig(level=logging.INFO)
TOKEN = "7546363316:AAEtCZQrvrAbsOFlRm6bd30r4Xjatlcw4_I"

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(location.router)

    dp.include_router(waste.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())