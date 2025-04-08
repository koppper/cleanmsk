from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from utils import get_message_template
from typing import List

async def get_keyboard(template_names: List[str]) -> ReplyKeyboardMarkup:
    keyboard = []

    row = []

    for name in template_names:
        if name == "start_game":
            row.append(KeyboardButton(
                text="🎮 Запустить игру",
                web_app=WebAppInfo(url="https://sorting-clean-moscow.ru/sort-game")
            ))
        else:
            text = await get_message_template(name)
            row.append(KeyboardButton(text=text))

    if row:
        keyboard.append(row)

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )
