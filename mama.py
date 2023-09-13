import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token='6584652808:AAGdp1-TcXf9RkHiiF9Fuji9w3c46do67Vo')
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Основные клавиши
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
button1 = KeyboardButton('Мои командировки')
main_keyboard.add(button1)

class States(StatesGroup):
    InBusinessTripsMenu = State()

# Создаем словарь для хранения командировок
business_trips_db = {
    1: "Командировка 1",
    2: "Командировка 2",
    3: "Командировка 3",
    4: "Командировка 4",
    5: "Командировка 5",
    6: "Командировка 6",
    7: "Командировка 7",
    8: "Командировка 8",
    9: "Командировка 9",
    10: "Командировка 10",
}

def generate_trips_paginator(trips, current_page):
    keyboard = InlineKeyboardMarkup()

    start_index = current_page * 5
    end_index = start_index + 5

    for trip_id in trips[start_index:end_index]:
        trip_name = business_trips_db.get(trip_id, "Название не найдено")
        keyboard.add(InlineKeyboardButton(text=trip_name, callback_data=f'trip:{trip_id}'))

    if current_page > 0:
        keyboard.add(InlineKeyboardButton(text='\u00AB', callback_data=f'paginate:prev_trips_page'))

    if end_index < len(trips):
        keyboard.add(InlineKeyboardButton(text='\u00BB', callback_data=f'paginate:next_trips_page'))

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))

    return keyboard

def generate_business_trips():
    return list(business_trips_db.keys())

@dp.message_handler(commands=['start'])
async def start_message_handler(message: types.Message):
    await bot.send_message(message.chat.id, "Выберите действие из предложенного списка:", reply_markup=main_keyboard)

async def display_business_trips(chat_id, trips, current_page):
    await bot.send_message(chat_id, "Выберите командировку:", reply_markup=generate_trips_paginator(trips, current_page))

@dp.message_handler(lambda message: message.text == button1.text, content_types=types.ContentType.TEXT)
async def my_business_trips_handler(message: types.Message, state: FSMContext):
    trips = generate_business_trips()
    await display_business_trips(message.chat.id, trips, current_page=0)
    await States.InBusinessTripsMenu.set()

@dp.message_handler(content_types=types.ContentType.TEXT, state="*")
async def text_handler_while_in_menu(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, "Пожалуйста, выберете командировку из меню.")

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Выберите действие из предложенного списка:", reply_markup=main_keyboard)
    await bot.answer_callback_query(callback_query.id)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('paginate:'), state="*")
async def process_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        current_trips_page = data.get('current_trips_page', 0)

        direction = callback_query.data.split(':')[1]

        if direction == 'prev_trips_page':
            current_trips_page = max(0, current_trips_page - 1)
        elif direction == 'next_trips_page':
            current_trips_page += 1

        data['current_trips_page'] = current_trips_page

        trips = generate_business_trips()
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id, reply_markup=generate_trips_paginator(trips, current_trips_page))

    await bot.answer_callback_query(callback_query.id)

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
