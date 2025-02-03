import config
API_KEY = config.OWM_API
BOT_TOKEN = config.token

import re
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from database.db import engine, async_session, create_tables
from database.models import Base, Place
from database.repository import UserRepository, PlaceRepository


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_coords = {}
current_actions = {}
user_last_message = {}

def get_wind_direction(deg: float | None) -> str:
    directions = ["⬇️ С", "↘️ СВ", "➡️ В", "↗️ ЮВ", "⬆️ Ю", "↖️ ЮЗ", "⬅️ З", "↙️ СЗ"]
    return directions[round(deg / 45) % 8] if deg else "н/д"

def get_day_name(date: datetime.date) -> str:
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    return days[date.weekday()]

async def build_main_menu(user_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    async with async_session() as session:
        user = await UserRepository.get_or_create(session, user_id)
        places = await PlaceRepository.get_all(session, user.id)
        
        for place in places:
            builder.button(
                text=f"📍 {place.name}", 
                callback_data=f"place_{place.id}"
            )
        
        builder.button(text="➕ Добавить место", callback_data="add_place")
        builder.button(text="🗑️ Удалить место", callback_data="delete_place")
        builder.button(text="🌤 Текущее местоположение", callback_data="current_location")
        
    builder.adjust(1, 2, 1)
    return builder

async def edit_or_resend(callback: types.CallbackQuery, text: str, reply_markup: types.InlineKeyboardMarkup = None) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
        user_last_message[callback.from_user.id] = callback.message.message_id
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        new_msg = await callback.message.answer(text, reply_markup=reply_markup)
        user_last_message[callback.from_user.id] = new_msg.message_id
    finally:
        await callback.answer()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with async_session() as session:
        await UserRepository.get_or_create(session, message.from_user.id)
    
    builder = await build_main_menu(message.from_user.id)
    msg = await message.answer("🌤 Выберите действие:", reply_markup=builder.as_markup())
    user_last_message[message.from_user.id] = msg.message_id

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    builder = await build_main_menu(callback.from_user.id)
    await edit_or_resend(callback, "🌤 Главное меню:", builder.as_markup())

@dp.callback_query(F.data == "current_location")
async def request_location(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    
    # Создаем клавиатуру с кнопкой геолокации и отмены
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [types.KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    msg = await callback.message.answer(
        "📍 Отправьте геолокацию или нажмите Отмена:",
        reply_markup=keyboard
    )
    user_last_message[callback.from_user.id] = msg.message_id

@dp.message(F.text == "❌ Отмена")
async def cancel_location_request(message: types.Message):
    user_id = message.from_user.id
    
    # Удаляем клавиатуру
    try:
        await bot.delete_message(message.chat.id, user_last_message[user_id])
    except TelegramBadRequest:
        pass
    
    # Удаляем сообщение с кнопкой отмены
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    # Возвращаем главное меню
    builder = await build_main_menu(user_id)
    msg = await message.answer("🌤 Главное меню:", reply_markup=builder.as_markup())
    user_last_message[user_id] = msg.message_id
    
async def edit_or_resend(callback: types.CallbackQuery, text: str, reply_markup: types.InlineKeyboardMarkup = None) -> None:
    try:
        # Пытаемся редактировать существующее сообщение
        await callback.message.edit_text(text, reply_markup=reply_markup)
        user_last_message[callback.from_user.id] = callback.message.message_id
    except TelegramBadRequest as e:
        # Если не получилось редактировать, отправляем новое сообщение
        if "message is not modified" not in str(e):
            new_msg = await callback.message.answer(text, reply_markup=reply_markup)
            user_last_message[callback.from_user.id] = new_msg.message_id
    finally:
        await callback.answer()
        
        
@dp.message(F.content_type == ContentType.LOCATION)
async def handle_location(message: types.Message):
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude
    user_coords[user_id] = (lat, lon)
    
    if user_id in user_last_message:
        try:
            await bot.delete_message(message.chat.id, user_last_message[user_id])
        except TelegramBadRequest:
            pass
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Сейчас", callback_data="current")
    builder.button(text="Сегодня", callback_data="today")
    builder.button(text="5 дней", callback_data="5days")
    builder.button(text="← Назад", callback_data="main_menu")
    builder.adjust(3)
    
    msg = await message.answer("Выберите тип прогноза:", reply_markup=builder.as_markup())
    user_last_message[user_id] = msg.message_id
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

@dp.callback_query(F.data == "add_place")
async def add_place_start(callback: types.CallbackQuery):
    current_actions[callback.from_user.id] = "adding_place"
    await edit_or_resend(
        callback,
        "Введите данные в формате:\n<Название>, <широта>, <долгота>\nПример: Дом, 55.7558, 37.6176",
        InlineKeyboardBuilder().button(text="← Назад", callback_data="main_menu").as_markup()
    )

@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if current_actions.get(user_id) == "adding_place":
        try:
            if user_id in user_last_message:
                try:
                    await bot.delete_message(message.chat.id, user_last_message[user_id])
                except TelegramBadRequest:
                    pass
            
            name, lat, lon = re.split(r"\s*,\s*", message.text, maxsplit=2)
            lat = float(lat)
            lon = float(lon)
            
            async with async_session() as session:
                user = await UserRepository.get_or_create(session, user_id)
                await PlaceRepository.create(session, user.id, name, lat, lon)
                await session.commit()
            
            del current_actions[user_id]
            builder = await build_main_menu(user_id)
            msg = await message.answer(f"✅ Место '{name}' добавлено!", reply_markup=builder.as_markup())
            user_last_message[user_id] = msg.message_id
            
        except Exception as e:
            msg = await message.answer(f"❌ Ошибка: {str(e)}")
            user_last_message[user_id] = msg.message_id
        finally:
            try:
                await message.delete()
            except TelegramBadRequest:
                pass

@dp.callback_query(F.data.startswith("place_"))
async def select_place(callback: types.CallbackQuery):
    place_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        user = await UserRepository.get_or_create(session, callback.from_user.id)
        place = await session.get(Place, place_id)
        
        if place and place.user_id == user.id:
            user_coords[callback.from_user.id] = (place.lat, place.lon)
            
            builder = InlineKeyboardBuilder()
            builder.button(text="Сейчас", callback_data="current")
            builder.button(text="Сегодня", callback_data="today")
            builder.button(text="5 дней", callback_data="5days")
            builder.button(text="← Назад", callback_data="main_menu")
            builder.adjust(3)
            
            await edit_or_resend(
                callback,
                f"📍 Выбрано: {place.name}",
                builder.as_markup()
            )
        else:
            await callback.answer("🚫 Это не ваше место!", show_alert=True)

@dp.callback_query(F.data == "delete_place")
async def delete_place_start(callback: types.CallbackQuery):
    async with async_session() as session:
        user = await UserRepository.get_or_create(session, callback.from_user.id)
        places = await PlaceRepository.get_all(session, user.id)
    
    if not places:
        await callback.answer("❌ У вас нет сохраненных мест", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for place in places:
        builder.button(text=f"❌ {place.name}", callback_data=f"delete_confirm_{place.id}")
    builder.button(text="← Назад", callback_data="main_menu")
    builder.adjust(1)
    
    await edit_or_resend(
        callback,
        "Выберите место для удаления:",
        builder.as_markup()
    )

@dp.callback_query(F.data.startswith("delete_confirm_"))
async def delete_place_confirm(callback: types.CallbackQuery):
    place_id = int(callback.data.split("_")[-1])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"delete_final_{place_id}")
    builder.button(text="❌ Нет", callback_data="main_menu")
    builder.adjust(2)
    
    await edit_or_resend(
        callback,
        "Вы уверены, что хотите удалить это место?",
        builder.as_markup()
    )

@dp.callback_query(F.data.startswith("delete_final_"))
async def delete_place_final(callback: types.CallbackQuery):
    place_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    async with async_session() as session:
        user = await UserRepository.get_or_create(session, user_id)
        success = await PlaceRepository.delete(session, place_id, user.id)
    
    if success:
        builder = await build_main_menu(user_id)
        await edit_or_resend(
            callback,
            "✅ Место успешно удалено!",
            builder.as_markup()
        )
    else:
        await edit_or_resend(
            callback,
            "❌ Не удалось удалить место",
            InlineKeyboardBuilder().button(text="← Назад", callback_data="main_menu").as_markup()
        )

@dp.callback_query(F.data.in_(["current", "today", "5days"]))
async def process_forecast(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_coords:
        await callback.answer("❌ Сначала выберите местоположение!", show_alert=True)
        return

    lat, lon = user_coords[user_id]
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru"
        
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(url) as response:
                if response.status != 200:
                    await callback.answer("⛈ Ошибка сервера. Попробуйте позже.", show_alert=True)
                    return
                
                forecast_data = await response.json()
                
                if callback.data == "current":
                    await send_current_weather(forecast_data, callback)
                elif callback.data == "today":
                    await send_daily_forecast(forecast_data, 1, callback)
                elif callback.data == "5days":
                    await send_daily_forecast(forecast_data, 5, callback)

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("⛈ Ошибка запроса. Попробуйте позже.", show_alert=True)

async def send_current_weather(data: dict, callback: types.CallbackQuery):
    if not data.get("list") or len(data["list"]) == 0:
        await callback.answer("❌ Нет данных о текущей погоде.", show_alert=True)
        return

    current = data["list"][0]
    temp = current["main"].get("temp", "н/д")
    humidity = current["main"].get("humidity", "н/д")  # Добавляем влажность
    desc = current["weather"][0].get("description", "н/д").capitalize()
    wind_speed = current["wind"].get("speed", "н/д")
    wind_deg = current["wind"].get("deg")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад", callback_data="main_menu")
    
    await edit_or_resend(
        callback,
        f"🌡 Сейчас: {temp}°C\n"
        f"💧 Влажность: {humidity}%\n"  # Новая строка
        f"🌪 Ветер: {wind_speed} м/с ({get_wind_direction(wind_deg)})\n"
        f"☁️ {desc}",
        builder.as_markup()
    )

async def send_daily_forecast(data: dict, days: int, callback: types.CallbackQuery):
    forecasts = {}
    for entry in data["list"]:
        date = datetime.fromtimestamp(entry["dt"]).date()
        forecasts.setdefault(date, []).append(entry)

    sorted_dates = sorted(forecasts.keys())
    response = []
    
    for date in sorted_dates[:days]:
        daily_entries = forecasts[date]
        day_name = get_day_name(date)
        
        if days == 1:
            response.append(f"📅 {day_name} ({date}):")
            for entry in daily_entries:
                time = datetime.fromtimestamp(entry["dt"]).strftime("%H:%M")
                temp = entry["main"]["temp"]
                humidity = entry["main"].get("humidity", "н/д")  # Добавляем влажность
                desc = entry["weather"][0]["description"].capitalize()
                wind_speed = entry["wind"]["speed"]
                wind_deg = entry["wind"].get("deg")
                response.append(
                    f"⏰ {time}:\n"
                    f"  🌡 {temp}°C\n"
                    f"  💧 {humidity}%\n"  # Новая строка
                    f"  🌪 {wind_speed} м/с ({get_wind_direction(wind_deg)})\n"
                    f"  ☁️ {desc}"
                )
        else:
            temp_min = min(e["main"]["temp_min"] for e in daily_entries)
            temp_max = max(e["main"]["temp_max"] for e in daily_entries)
            humidity_avg = round(sum(e["main"].get("humidity", 0) for e in daily_entries) / len(daily_entries))  # Средняя влажность
            wind_speeds = [e["wind"]["speed"] for e in daily_entries]
            wind_deg = daily_entries[0]["wind"].get("deg")
            desc = daily_entries[0]["weather"][0]["description"].capitalize()
            
            response.append(
                f"📅 {day_name} ({date}):\n"
                f"  🌡 {temp_min}°C...{temp_max}°C\n"
                f"  💧 Влажность: ~{humidity_avg}%\n"  # Новая строка
                f"  🌪 Ветер: до {max(wind_speeds)} м/с ({get_wind_direction(wind_deg)})\n"
                f"  ☁️ {desc}"
            )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад", callback_data="main_menu")
    
    await edit_or_resend(
        callback,
        "\n\n".join(response),
        builder.as_markup()
    )
    
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

dp.startup.register(on_startup)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))