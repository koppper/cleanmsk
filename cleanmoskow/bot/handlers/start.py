from aiogram import types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Router
from keyboards import get_keyboard
from utils import get_message_template, register_user

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user, created = await register_user(message.from_user.id, message.from_user.username)

    # if created:
    #     greeting = await get_message_template("new_user_registered")
    # else:
    #     greeting = await get_message_template("welcome_back")
    # text = await get_message_template("welcome_back")
    template_text = await get_message_template("start_message")
    kb = await get_keyboard(["search_points_button_text"])

    await message.answer(f"{template_text}", reply_markup=kb)