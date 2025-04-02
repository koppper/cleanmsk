from aiogram.enums import ContentType
from geopy.distance import geodesic
from asgiref.sync import sync_to_async
from api.models import Category, Points
from accounts.models import User
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from utils import get_message_template, register_user
from keyboards import get_keyboard
from aiogram import Router
from accounts.utils import log_user_action
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()
from accounts.models import UserActivity, User

async def log_user_action_by_telegram_id(telegram_id, action):
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=telegram_id)
        await sync_to_async(UserActivity.objects.create)(user=user, action=action)
    except User.DoesNotExist:
        pass


@router.message(F.content_type == ContentType.LOCATION)
async def handle_location(message: types.Message, state: FSMContext):
    print("GEO ХЕНДЛЕР СРАБОТАЛ")
    await log_user_action_by_telegram_id(message.from_user.id, "location_request")

    # await message.answer("Я получил твою геолокацию!")
    latitude = message.location.latitude
    longitude = message.location.longitude

    await state.update_data(location={"latitude": latitude, "longitude": longitude})
    user_data = await state.get_data()
    waste_type = user_data.get("waste_type")

    if not waste_type:
        text = await get_message_template("choose_waste")
        kb = await get_keyboard([
            "recyclable_button", "mixed_button", "hazardous_button"
        ])
        await message.answer(text, reply_markup=kb)

    if latitude is None or longitude is None:
        text = await get_message_template("request_location")
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=await get_message_template("send_location_button"), request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(text, reply_markup=kb)
        return

    try:
        category = await sync_to_async(Category.objects.filter(name_ru=waste_type).first)()

        if not category:
            await message.answer("❗️ Категория не найдена.")
            text = await get_message_template("choose_waste")
            kb = await get_keyboard([
                "recyclable_button", "mixed_button", "hazardous_button"
            ])
            await message.answer(text, reply_markup=kb)
            return


        points = await sync_to_async(lambda: list(Points.objects.filter(categories__icontains=category)))()

        if not points:
            await message.answer("❗️ Нет доступных пунктов для выбранной категории.")
            text = await get_message_template("choose_waste")
            kb = await get_keyboard([
                "recyclable_button", "mixed_button", "hazardous_button"
            ])
            await message.answer(text, reply_markup=kb)
            return

        nearest_point, distance = await find_nearest_point(latitude, longitude, points)

        if not nearest_point:
            await message.answer("❗️ Ближайший пункт не найден.")
            return

        if not nearest_point.businesHoursState:
            import logging
            logging.warning(f"📌 Пункт без расписания: {nearest_point.title} (ID: {nearest_point.id})")
            await message.answer("❗️ Ближайший пункт не найден.")
            return

        schedule_text = "Пункт работает:\n"
        for day, hours in nearest_point.businesHoursState.items():
            schedule_text += f"{day}: {hours}\n"

        await message.answer_location(latitude=nearest_point.latitude, longitude=nearest_point.longitude)

        response = (
            f"Адрес: {nearest_point.address}\n"
            f"{nearest_point.title}\n"
            f"Принимается старая техника: {nearest_point.description}\n"
            f"Часы работы:\n"
            # f"📍 {nearest_point.title}\n"
            # f"🏠 Адрес: {nearest_point.address}\n"
            # f"ℹ️ Описание: {nearest_point.description}\n"
            # f"📏 Расстояние: {distance:.2f} км\n"
            f"{schedule_text}"
        )

        user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)
        user.location_requests_count += 1
        await sync_to_async(user.save)()

        kb = await get_keyboard(["choose_other_point_button_text", "show_nearby_points_button_text"])

        await message.answer(response, reply_markup=kb)

    except Exception as e:
        import logging
        logging.exception("Ошибка при обработке геолокации")
        text = await get_message_template("choose_waste")
        kb = await get_keyboard([
            "recyclable_button", "mixed_button", "hazardous_button"
        ])
        await message.answer(text, reply_markup=kb)

async def find_nearest_point(user_lat, user_lon, points):
    nearest_point = None
    min_distance = float("inf")
    for point in points:
        distance = geodesic((user_lat, user_lon), (point.latitude, point.longitude)).km
        if distance < min_distance:
            min_distance = distance
            nearest_point = point
    return nearest_point, min_distance


@router.message(lambda msg: msg.text == "Показать пункты рядом")
async def near_locations(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    waste_type = user_data.get("waste_type", "Не выбрано")
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

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        text = await get_message_template("request_location")
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=await get_message_template("send_location_button"), request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(text, reply_markup=kb)
        return

    try:
        category = await sync_to_async(Category.objects.filter(name_ru=waste_type).first)()
        if not category:
            await message.answer("❗️ Категория не найдена.")
            text = await get_message_template("choose_waste")
            kb = await get_keyboard([
                "recyclable_button", "mixed_button", "hazardous_button"
            ])
            await message.answer(text, reply_markup=kb)
            return

        points = await sync_to_async(lambda: list(Points.objects.filter(categories__icontains=category)))()
        if not points:
            await message.answer("❗️ Нет доступных пунктов для выбранной категории.")
            text = await get_message_template("choose_waste")
            kb = await get_keyboard([
                "recyclable_button", "mixed_button", "hazardous_button"
            ])
            await message.answer(text, reply_markup=kb)
            return

        points_with_distance = [
            (point, geodesic((latitude, longitude), (point.latitude, point.longitude)).km)
            for point in points
        ]

        sorted_points = sorted(points_with_distance, key=lambda x: x[1])
        top_nearest_points = sorted_points[:3]

        points_count = len(points_with_distance)
        showing_count = len(top_nearest_points)

        header = "Другие пункты рядом:\n"
        # if points_count > 3:
        #     header += f"Показываем ближайшие {showing_count}:\n\n"
        # else:
        #     header += f"Показываем все найденные пункты:\n\n"

        response_text = header

        for point, distance in top_nearest_points:
            if not point.businesHoursState:
                continue

            schedule_text = "Пункт работает:\n"
            for day, hours in point.businesHoursState.items():
                schedule_text += f"{day}: {hours}\n"

            response_text += (
                # f"🏠 {point.title}\n"
                # f"📍 Адрес: {point.address}\n"
                # f"ℹ️ Описание: {point.description}\n"
                # f"📏 Расстояние: {distance:.2f} км\n"
                f"Адрес: {point.address}\n"
                f"{point.title}\n"
                f"Принимается старая техника: {point.description}\n"
                f"Часы работы:\n"
                # f"Пункт работает:\n"
                f"{schedule_text}\n\n"
            )

        kb = await get_keyboard(["choose_other_point_button_text"])

        user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)
        user.location_requests_count += 1
        await sync_to_async(user.save)()

        await message.answer(response_text, reply_markup=kb)

    except Exception as e:
        print(f"❌ Ошибка при поиске ближайших пунктов: {e}")
        await message.answer("❌ Произошла ошибка при поиске ближайших пунктов.")

        # Показываем выбор категорий
        text = await get_message_template("choose_waste")
        kb = await get_keyboard([
            "recyclable_button", "mixed_button", "hazardous_button"
        ])
        await message.answer(text, reply_markup=kb)
