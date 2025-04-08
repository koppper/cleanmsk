from aiogram import types, Router
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from geopy.distance import geodesic
from asgiref.sync import sync_to_async

from utils import get_all_templates, get_message_template
from keyboards import get_keyboard
from api.models import Category, Points
from accounts.models import User, UserActivity

import logging

router = Router()
logger = logging.getLogger(__name__)

@sync_to_async
def log_user_action(telegram_id: int, action: str):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        UserActivity.objects.create(user=user, action=action)
    except User.DoesNotExist:
        pass

@sync_to_async
def find_category(name_ru: str):
    return Category.objects.filter(name_ru=name_ru).first()

@sync_to_async
def get_points_by_category(category):
    return list(Points.objects.filter(categories__icontains=category))

async def find_nearest_point(user_lat, user_lon, points):
    nearest_point = None
    min_distance = float("inf")
    for point in points:
        distance = geodesic((user_lat, user_lon), (point.latitude, point.longitude)).km
        if distance < min_distance:
            min_distance = distance
            nearest_point = point
    return nearest_point, min_distance

@router.message()
async def universal_message_handler(message: types.Message, state: FSMContext):
    if message.text and message.text.startswith("/start"):
        return

    if message.content_type == ContentType.LOCATION:
        await log_user_action(message.from_user.id, "location_request")

        latitude = message.location.latitude
        longitude = message.location.longitude
        await state.update_data(location={"latitude": latitude, "longitude": longitude})

        user_data = await state.get_data()
        waste_type = user_data.get("waste_type")

        if not waste_type:
            text = await get_message_template("choose_waste")
            kb = await get_keyboard(["recyclable_button", "mixed_button", "hazardous_button"])
            await message.answer(text, reply_markup=kb)
            return

        category = await find_category(waste_type)
        if not category:
            await message.answer("❗️ Категория не найдена.")
            return

        points = await get_points_by_category(category)
        if not points:
            await message.answer("❗️ Нет доступных пунктов.")
            return

        nearest_point, _ = await find_nearest_point(latitude, longitude, points)
        if not nearest_point or not nearest_point.businesHoursState:
            await message.answer("❗️ Ближайший пункт не найден.")
            return

        schedule_text = ""
        if isinstance(nearest_point.businesHoursState, dict):
            is_24_7 = all(v == "00:00 - 23:59" for v in nearest_point.businesHoursState.values())
            if is_24_7:
                schedule_text = "Круглосуточно"
            else:
                for day, hours in nearest_point.businesHoursState.items():
                    schedule_text += f"{day}: {hours}\n"
        elif isinstance(nearest_point.businesHoursState, str):
            schedule_text = nearest_point.businesHoursState

        await message.answer_location(latitude=nearest_point.latitude, longitude=nearest_point.longitude)

        response = (
            f"Адрес: {nearest_point.address}\n"
            f"{nearest_point.title or ''}\n"
            f"{'Ссылка: ' + nearest_point.link if nearest_point.link else ''}\n"
            f"{nearest_point.description or ''}\n"
            f"Часы работы:\n{schedule_text}"
        )

        user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)
        user.location_requests_count += 1
        await sync_to_async(user.save)()

        kb = await get_keyboard(["choose_other_point_button_text", "show_nearby_points_button_text", "return_to_main"])
        await message.answer(response, reply_markup=kb)
        return

    search_text = await get_message_template("search_points_button_text")
    choose_other_text = await get_message_template("choose_other_point_button_text")
    show_nearby_text = await get_message_template("show_nearby_points_button_text")

    if message.text == show_nearby_text:
        user_data = await state.get_data()
        waste_type = user_data.get("waste_type")
        location = user_data.get("location")
        if not location:
            text = await get_message_template("request_location")
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=await get_message_template("send_location_button"), request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await message.answer(text, reply_markup=kb)
            return

        latitude = location["latitude"]
        longitude = location["longitude"]
        category = await find_category(waste_type)
        if not category:
            await message.answer("❗️ Категория не найдена.")
            return

        points = await get_points_by_category(category)
        top_points = sorted([
            (point, geodesic((latitude, longitude), (point.latitude, point.longitude)).km)
            for point in points
        ], key=lambda x: x[1])[:3]

        if not top_points:
            await message.answer("❗️ Нет ближайших пунктов.")
            return



        response = "Другие пункты рядом:\n\n"
        for point, _ in top_points:
            # schedule_text = ""
            # if isinstance(point.businesHoursState, dict):
            #     for day, hours in point.businesHoursState.items():
            #         schedule_text += f"{day}: {hours}\n"
            # elif isinstance(point.businesHoursState, str):
            #     schedule_text = point.businesHoursState
            schedule_text = ""
            if isinstance(point.businesHoursState, dict):
                is_24_7 = all(v == "00:00 - 23:59" for v in point.businesHoursState.values())
                if is_24_7:
                    schedule_text = "Круглосуточно"
                else:
                    for day, hours in point.businesHoursState.items():
                        schedule_text += f"{day}: {hours}\n"
            elif isinstance(point.businesHoursState, str):
                schedule_text = point.businesHoursState

            response += (
                f"Адрес: {point.address}\n"
                f"{point.title or ''}\n"
                f"{'Ссылка: ' + point.link if point.link else ''}\n"
                f"{point.description or ''}\n"
                f"Часы работы:\n{schedule_text}\n\n"
            )

        kb = await get_keyboard(["choose_other_point_button_text"])
        user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)
        user.location_requests_count += 1
        await sync_to_async(user.save)()
        await message.answer(response, reply_markup=kb)
        return

    if message.text in [search_text, choose_other_text]:
        text = await get_message_template("choose_waste")
        kb = await get_keyboard(["recyclable_button", "mixed_button", "hazardous_button"])
        await message.answer(text, reply_markup=kb)
        return

    hazardous = await get_message_template("hazardous_button")
    recyclable = await get_message_template("recyclable_button")
    mixed = await get_message_template("mixed_button")
    if message.text == hazardous:
        response = await get_message_template("hazardous_waste")
        # kb = await get_keyboard(["thermometer_button", "battery_button", "bulb_button"])
        kb = await get_keyboard(["battery_button", "bulb_button"])
        await message.answer(response, reply_markup=kb)
        return
    elif message.text in [recyclable, mixed]:
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

    templates = await get_all_templates()
    matched_template = next((t for t in templates if t.text.strip() == message.text.strip()), None)

    if matched_template:
        await message.answer(f"🔹 Название шаблона: *{matched_template.name}*", parse_mode="Markdown")
    else:
        await message.answer("⚠️ Я не нашёл шаблон для этого сообщения.", reply_markup=ReplyKeyboardRemove())
