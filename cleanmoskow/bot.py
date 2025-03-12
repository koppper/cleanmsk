import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
import os
import sys
import django
from asgiref.sync import sync_to_async
import requests
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from geopy.distance import geodesic
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
sys.path.append('/home/moskow/cleanmoskow')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cleanmoskow.settings")

django.setup()

from api.models import MessageTemplate, User, Category, Points


TOKEN = "7943017558:AAEFHuEPV8VcLdTVPbzeWVIJIAj0tSc6Lmg"
bot = Bot(token=TOKEN)
dp = Dispatcher()

class WasteState(StatesGroup):
    waste_type = State()


async def get_message_template(name):
    try:
        logger.debug(f"Запрашиваем шаблон сообщения: {name}")
        template = await sync_to_async(MessageTemplate.objects.get)(name=name)
        return template.text
    except MessageTemplate.DoesNotExist:
        logger.error(f"Шаблон {name} не найден в БД")
        return "Шаблон с таким именем не найден."


start_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Начать")]], resize_keyboard=True)


from aiogram.filters import CommandStart

@dp.message(CommandStart())
async def start(message: types.Message):
    print("Starting TG BOT")
    user, created = await register_user(message.from_user.id, message.from_user.username)

    if created:
        text = "Вы успешно зарегистрированы! 🎉"
    else:
        text = "С возвращением! 👋"

    print("lol")  # Для отладки, убедись, что этот print вообще выполняется
    
    template_text = await get_message_template("start_message")

    # Клавиатура для старта
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поиск пунктов сбора отходов")],
            [KeyboardButton(text="Mini App")]
        ],
        resize_keyboard=True
    )

    await message.answer(f"{text}\n\n{template_text}", reply_markup=kb)




@dp.message(lambda msg: msg.text in ["Поиск пунктов сбора отходов", "Выбрать другой пункт"])
async def show_options(message: types.Message, state: FSMContext):

    text = await get_message_template("choose_waste")
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Втор. сырьё")],
            [KeyboardButton(text="Смешанные отходы")],
            [KeyboardButton(text="Опасные отходы")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)


@dp.message(lambda msg: msg.text == "Опасные отходы")
async def hazardous_waste(message: types.Message):
    text = await get_message_template("hazardous_waste")
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Градусник")],
            [KeyboardButton(text="Батарейка")],
            [KeyboardButton(text="Лампочка")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)


@dp.message(lambda msg: msg.text in ["Градусник", "Батарейка", "Лампочка", "Втор. сырьё", "Смешанные отходы"])
async def request_location(message: types.Message, state: FSMContext):
    await state.update_data(waste_type=message.text)
    text = await get_message_template("request_location")
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить геопозицию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(text, reply_markup=kb)


async def get_address_from_coordinates(latitude, longitude):
    """Функция для получения адреса по координатам"""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, lambda: requests.get(url, headers={"User-Agent": "TelegramBot"}))
        data = response.json()
        return data.get("display_name", "Адрес не найден")
    except Exception as e:
        return "Ошибка определения адреса"




async def find_nearest_point(user_lat, user_lon, points):
    print("user: ",user_lat, user_lon, points)
    nearest_point = None
    min_distance = float("inf")
    for point in points:
        point_lat = point.latitude
        point_lon = point.longitude
        print("point: ", point_lat, point_lon)

        distance = geodesic((user_lat, user_lon), (point_lat, point_lon)).km
        if distance < min_distance:
            min_distance = distance
            nearest_point = point

    return nearest_point, min_distance


@dp.message(F.content_type == ContentType.LOCATION)
async def send_nearest_location(message: types.Message, state: FSMContext):
    latitude, longitude = message.location.latitude, message.location.longitude
    logger.info(f"📍 Получена геолокация от {message.from_user.id}: {latitude}, {longitude}")
    await state.update_data(location={"latitude": latitude, "longitude": longitude})

    user_data = await state.get_data()
    waste_type = user_data.get("waste_type")

    if not waste_type:
        logger.warning(f"⚠️ Пользователь {message.from_user.id} отправил геолокацию без выбора типа отходов")
        await message.answer("❗️ Вы не выбрали тип отходов. Пожалуйста, выберите перед отправкой геолокации.")
        return

    logger.debug(f"🗑 Тип отходов: {waste_type}")

    # Проверяем валидность координат
    if latitude is None or longitude is None:
        logger.error(f"⛔️ Неверные координаты от пользователя {message.from_user.id}")
        await message.answer(await get_message_template("resend_geo"))
        return

    text = await get_message_template("near_locations")

    try:
        category = await sync_to_async(Category.objects.filter(name_ru=waste_type).first)()

        if not category:
            logger.error(f"🚫 Категория '{waste_type}' не найдена в БД")
            await message.answer("❗️ Категория не найдена.")
            return

        logger.debug(f"✅ Найдена категория: {category}")

        points = await sync_to_async(lambda: list(Points.objects.filter(categories__icontains=category)))()

        if not points:
            logger.warning(f"⚠️ Для категории '{waste_type}' нет доступных пунктов.")
            await message.answer("❗️ Нет доступных пунктов для выбранной категории.")
            return

        nearest_point, distance = await find_nearest_point(latitude, longitude, points)

        if not nearest_point:
            logger.warning("❌ Ближайший пункт не найден.")
            await message.answer("❗️ Ближайший пункт не найден.")
            return

        # Карта дней недели (английский -> русский)
        weekdays_map = {
            "Monday": "пн",
            "Tuesday": "вт",
            "Wednesday": "ср",
            "Thursday": "чт",
            "Friday": "пт",
            "Saturday": "сб",
            "Sunday": "вс",
        }

        schedule_text = "🕒 Пункт работает:\n"
        for en_day, ru_day in weekdays_map.items():
            hours = nearest_point.businesHoursState.get(en_day, "не работает") if nearest_point.businesHoursState else "не работает"
            schedule_text += f"{ru_day}: {hours}\n"

        response_text = (
            f"📍 {nearest_point.title}\n"
            f"🏠 Адрес: {nearest_point.address}\n"
            f"ℹ️ Описание: {nearest_point.description}\n"
            f"📏 Расстояние: {distance:.2f} км\n"
            f"{schedule_text}"
        )

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Выбрать другой пункт")],
                [KeyboardButton(text="Показать пункты рядом")]
            ],
            resize_keyboard=True
        )
        # 🔹 Находим пользователя и увеличиваем счетчик
        user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)
        user.location_requests_count += 1
        await sync_to_async(user.save)()

        logger.info(f"✅ Пользователь {message.from_user.id} запрашивал геолокацию {user.location_requests_count} раз(а)")

        await message.answer(response_text, reply_markup=kb)
        logger.info(f"✅ Отправлен ближайший пункт пользователю {message.from_user.id}: {nearest_point.title}")

    except Exception as e:
        logger.exception(f"❌ Ошибка при поиске ближайших пунктов: {e}")
        await message.answer("❌ Произошла ошибка при поиске ближайших пунктов.")

        # await message.answer("Произошла ошибка при поиске ближайших пунктов.")
        #             await message.answer(text=
        #                 f"{nearest_point.title}\n"
        #                 f"Адрес: {nearest_point.address}\n"
        #                 f"Название: {nearest_point.title}\n"
        #                 f"Описание: {nearest_point.description}\n"
        #                 f"Пункт работает: {schedule_text}\n",
        #                 reply_markup=kb
        #             )

@dp.message(lambda msg: msg.text == "Показать пункты рядом")
async def near_locations(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    waste_type = user_data.get("waste_type", "Не выбрано")
    location = user_data.get("location")
    print(f"user location: {location}")

    if not location:
        await message.answer(await get_message_template("not_send_geo"))
        return

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        await message.answer(await get_message_template("resend_geo"))
        return

    try:
        category = await sync_to_async(Category.objects.filter(name_ru=waste_type).first)()
        if not category:
            logger.error(f"🚫 Категория '{waste_type}' не найдена в БД")
            await message.answer("❗️ Категория не найдена.")
            return
        points = await sync_to_async(lambda: list(Points.objects.filter(categories__icontains=category)))()
        if not points:
            logger.warning(f"⚠️ Для категории '{waste_type}' нет доступных пунктов.")
            await message.answer("❗️ Нет доступных пунктов для выбранной категории.")
            return

        points_with_distance = [
            (point, geodesic((latitude, longitude), (point.latitude, point.longitude)).km)
            for point in points
        ]

        # Сортируем по расстоянию и берём только 3 ближайших
        top_nearest_points = sorted(points_with_distance, key=lambda x: x[1])[:3]

        if top_nearest_points:
            response_text = "📍 Три ближайших пункта:\n\n"
            weekdays_map = {
                "Monday": "пн",
                "Tuesday": "вт",
                "Wednesday": "ср",
                "Thursday": "чт",
                "Friday": "пт",
                "Saturday": "сб",
                "Sunday": "вс",
            }

            for point, distance in top_nearest_points:
                # Формируем текст расписания
                schedule_text = "Пункт работает:\n"
                for en_day, ru_day in weekdays_map.items():
                    hours = point.businesHoursState.get(en_day, "не работает")
                    schedule_text += f"{ru_day}: {hours}\n"

                response_text += (
                    f"🏠 {point.title}\n"
                    f"📍 Адрес: {point.address}\n"
                    f"ℹ️ Описание: {point.description}\n"
                    f"📏 Расстояние: {distance:.2f} км\n"
                    f"🕒 {schedule_text}\n"
                )
                kb = ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text="Выбрать другой пункт")],
                        ],
                        resize_keyboard=True
                    )
                user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)
                user.location_requests_count += 1
                await sync_to_async(user.save)()

                logger.info(f"✅ Пользователь {message.from_user.id} запрашивал геолокацию {user.location_requests_count} раз(а)")

                await message.answer(response_text, reply_markup=kb)
    except Exception as e:
        logger.exception(f"❌ Ошибка при поиске ближайших пунктов: {e}")
        await message.answer("❌ Произошла ошибка при поиске ближайших пунктов.")


async def main():
    print("Starting")
    await dp.start_polling(bot, skip_updates=False)


async def register_user(telegram_id, username):
    user, created = await sync_to_async(User.objects.get_or_create)(
        telegram_id=telegram_id,
        defaults={"username": username}
    )
    return user, created


if __name__ == "__main__":
    asyncio.run(main())