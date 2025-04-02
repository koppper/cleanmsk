from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils import get_message_template
from typing import List

async def get_keyboard(template_names: List[str]) -> ReplyKeyboardMarkup:
    keyboard = []
    for name in template_names:
        text = await get_message_template(name)
        keyboard.append([KeyboardButton(text=text)])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
