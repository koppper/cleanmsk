from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils import get_message_template
from keyboards import get_keyboard

router = Router()

@router.message(lambda msg: msg.text in ["Поиск пунктов сбора отходов", "Выбрать другой пункт"])
async def show_waste_options(message: types.Message, state: FSMContext):
    text = await get_message_template("choose_waste")
    kb = await get_keyboard([
        "recyclable_button", "mixed_button", "hazardous_button"
    ])
    await message.answer(text, reply_markup=kb)


@router.message()
async def handle_waste_type(message: types.Message, state: FSMContext):
    hazardous_text = await get_message_template("hazardous_button")
    mixed_text = await get_message_template("mixed_button")
    recyclable_text = await get_message_template("recyclable_button")

    if message.text == hazardous_text:
        response = await get_message_template("hazardous_waste")
        kb = await get_keyboard([
            "thermometer_button", "battery_button", "bulb_button"
        ])
        await message.answer(response, reply_markup=kb)
        return

    elif message.text in [mixed_text, recyclable_text]:
        await state.update_data(waste_type=message.text)
        response = await get_message_template("request_location")
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=await get_message_template("send_location_button"), request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(response, reply_markup=kb)
        return

    thermometer = await get_message_template("thermometer_button")
    battery = await get_message_template("battery_button")
    bulb = await get_message_template("bulb_button")

    if message.text in [thermometer, battery, bulb]:
        await state.update_data(waste_type=message.text)
        response = await get_message_template("request_location")
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=await get_message_template("send_location_button"), request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(response, reply_markup=kb)
        return
