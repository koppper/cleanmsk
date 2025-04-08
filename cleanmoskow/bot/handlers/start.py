from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram import Router
from keyboards import get_keyboard
from utils import get_message_template, register_user

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user, created = await register_user(message.from_user.id, message.from_user.username)
    template_text = await get_message_template("start_message")

    kb = await get_keyboard([
        "search_points_button_text", "start_game",
    ])
    await message.answer(f"{template_text}", reply_markup=kb)


@router.message(lambda msg: msg.text == "В главное меню")
async def return_to_main_menu(message: Message):
    await start(message)