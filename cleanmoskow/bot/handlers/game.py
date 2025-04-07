from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("play"))
async def send_game_link(msg: types.Message):
    user_id = msg.from_user.id
    first_name = msg.from_user.first_name

    game_url = f"https://sorting-clean-moscow.ru/sort-game"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Начать игру (Mini App)",
                    url=game_url
                )
            ]
        ]
    )

    await msg.answer(
        text="Нажми, чтобы запустить мини-приложение и передать UID",
        reply_markup=keyboard
    )
