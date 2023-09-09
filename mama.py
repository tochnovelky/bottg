import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token='6584652808:AAGdp1-TcXf9RkHiiF9Fuji9w3c46do67Vo')
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Создание основной клавиатуры
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
button1 = KeyboardButton('Мои командировки')
button2 = KeyboardButton('Добавить расходы')
button3 = KeyboardButton('Новая командировка')
button4 = KeyboardButton('Завершить командировку')
button5 = KeyboardButton('Как пользоваться')
main_keyboard.add(button1, button2, button3, button4, button5)

# Создание клавиатуры расходов
expenses_keyboard = InlineKeyboardMarkup()
expenses_keyboard.add(
    InlineKeyboardButton(text="Билеты", callback_data="tickets"),
    InlineKeyboardButton(text="Проживание", callback_data="accommodation"),
    InlineKeyboardButton(text="Представительские расходы", callback_data="entertainment"),
)

expense_type = None

# Создание переменной для хранения открытых командировок
open_trips = {}

# Функция для запроса суммы расхода у пользователя
async def ask_expense_amount(chat_id, expense_name):
    global expense_type
    expense_type = expense_name
    cancel_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_button.add(KeyboardButton('Отменить'))
    await bot.send_message(chat_id, f"Добавляем статью расхода: {expense_name}\nУкажите сумму:", reply_markup=cancel_button)

# Обработчик для кнопки "Отменить"
@dp.message_handler(lambda message: message.text == 'Отменить')
async def cancel_handler(message: types.Message):
    global expense_type
    expense_type = None
    await bot.send_message(message.chat.id, "Ввод данных отменен", reply_markup=main_keyboard)


# Обработчик нажатий кнопок расходов
@dp.callback_query_handler(lambda c: c.data in ["tickets", "accommodation", "entertainment"])
async def process_expense_buttons(callback_query: types.CallbackQuery):
    data = callback_query.data

    if data == 'tickets':
        expense_name = "Билеты"
    elif data == 'accommodation':
        expense_name = "Проживание"
    elif data == 'entertainment':
        expense_name = "Представительские расходы"

    await ask_expense_amount(callback_query.from_user.id, expense_name)
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(lambda message: message.text and expense_type, content_types=types.ContentType.TEXT)
async def amount_input_handler(message: types.Message):
    global expense_type

    try:
        amount = float(message.text)
        cancel_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        cancel_button.add(KeyboardButton('Отменить'))
        await bot.send_message(message.chat.id, f"Добавляем статью расхода: {expense_type}\nСумма: {amount}\nПрикрепите фото чека:", reply_markup=cancel_button)
    except ValueError:
        await bot.send_message(message.chat.id, "Некорректное значение суммы. Введите число:")

# Обработчик сообщений с фотографиями чеков для статей расходов
@dp.message_handler(lambda message: message.photo != None and expense_type, content_types=types.ContentType.PHOTO)
async def photo_handler(message: types.Message):
    global expense_type
    await bot.send_message(message.chat.id, f"Статья расхода: {expense_type}\nСумма уже введена\nФото чека добавлено.", reply_markup=main_keyboard)
    expense_type = None

# Функция для генерации клавиатуры с открытыми командировками
def generate_open_trips_keyboard():
    keyboard = InlineKeyboardMarkup()
    for key, value in open_trips.items():
        keyboard.add(InlineKeyboardButton(text=value, callback_data=f"open_trip:{key}"))
    return keyboard

# Функция для генерации пагинатора список командировок
def generate_trips_paginator(trips, current_page):
    keyboard = InlineKeyboardMarkup()
    for trip in trips[current_page * 5:(current_page * 5) + 5]:
        keyboard.add(InlineKeyboardButton(text=trip, callback_data=f'trip:{trip}'))

    if current_page > 0:
        keyboard.add(InlineKeyboardButton(text='\u00AB', callback_data=f'prev_trips_page:{current_page - 1}'))

    if len(trips) > (current_page + 1) * 5:
        keyboard.add(InlineKeyboardButton(text='\u00BB', callback_data=f'next_trips_page:{current_page + 1}'))

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))

    return keyboard

# Функция для отображения списка командировок пользователя
async def display_business_trips(chat_id, trips, current_page):
    await bot.send_message(chat_id, "Выберите командировку:", reply_markup=generate_trips_paginator(trips, current_page))

# Функция для генерации списка командировок (заглушка)
def generate_business_trips():
    trips = [f'Командировка {i}' for i in range(1, 11)]
    return trips

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_message_handler(message: types.Message):
    await bot.send_message(message.chat.id, "Выберите действие из предложенного списка:", reply_markup=main_keyboard)

# Обработчик неизвестных команд
@dp.message_handler(lambda message: message.text not in [button1.text, button2.text, button3.text, button4.text, button5.text], content_types=types.ContentType.TEXT)
async def text_message_handler(message: types.Message):
    await bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите действие из предложенного списка:", reply_markup=main_keyboard)

# Обработчик нажатий кнопок основного меню
@dp.message_handler(lambda message: message.text in [button1.text, button2.text, button3.text, button4.text, button5.text], content_types=types.ContentType.TEXT)
async def menu_buttons_handler(message: types.Message):
    if message.text == button1.text:
        trips = generate_business_trips()
        await display_business_trips(message.chat.id, trips, current_page=0)
    elif message.text == button2.text:
        await bot.send_message(message.chat.id, "Выберите статью расходов:", reply_markup=expenses_keyboard)
    elif message.text == button3.text:
        await bot.send_message(message.chat.id, "Укажите дату начала командировки в формате ДД.ММ.ГГ")
    elif message.text == button4.text:
        if open_trips:
            await bot.send_message(message.chat.id, "У вас есть открытые командировки:", reply_markup=generate_open_trips_keyboard())
        else:
            await bot.send_message(message.chat.id, "У вас нет открытых командировок.", reply_markup=main_keyboard)
    elif message.text == button5.text:
        await bot.send_message(message.chat.id, "Как пользоваться ботом?", reply_markup=main_keyboard)

# Обработчик ввода даты начала командировки
@dp.message_handler(lambda message: message.reply_to_message and message.reply_to_message.text.endswith("формате ДД.ММ.ГГ"), content_types=types.ContentType.TEXT)
async def date_input_handler(message: types.Message):
    entered_date = message.text
    try:
        start_date = datetime.strptime(entered_date, "%d.%m.%Y")
        # Добавляем командировку
        open_trip_id = len(open_trips) + 1
        open_trip_name = f"{entered_date}-"
        open_trips[open_trip_id] = open_trip_name
        await bot.send_message(message.chat.id, f"Командировка успешно создана с именем: {open_trip_name}", reply_markup=main_keyboard)
    except:
        await bot.send_message(message.chat.id, "Неверный формат. Укажите дату начала командировки в формате ДД.ММ.ГГ", reply_markup=main_keyboard)

# Обработчик нажатий на кнопки Inline с открытыми командировками
@dp.callback_query_handler(lambda c: c.data.startswith("open_trip:"))
async def open_trips_handler(callback_query: types.CallbackQuery):
    trip_id = int(callback_query.data[10:])
    trip_name = open_trips[trip_id]
    date = trip_name[:-1] # удаляем "-"
    month_year = datetime.strptime(date, "%d.%m.%Y").strftime("%B %Y")
    await bot.send_message(callback_query.from_user.id, f"Командировка: {month_year}\nДата начала: {date}\nУкажите дату закрытия:")
    await bot.answer_callback_query(callback_query.id)

# Обработчик ввода даты закрытия командировки
@dp.message_handler(lambda message: message.reply_to_message and message.reply_to_message.text.startswith("Командировка:"), content_types=types.ContentType.TEXT)
async def close_trip_date_handler(message: types.Message):
    entered_date = message.text
    try:
        end_date = datetime.strptime(entered_date, "%d.%m.%Y")
        await bot.send_message(message.chat.id, "Командировка успешно завершена", reply_markup=main_keyboard)
    except:
        await bot.send_message(message.chat.id, "Неверный формат. Укажите дату закрытия командировки в формате ДД.ММ.ГГ", reply_markup=main_keyboard)

# Обработчик кнопки возврата в основное меню
@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Выберите действие из предложенного списка:", reply_markup=main_keyboard)
    await bot.answer_callback_query(callback_query.id)

# Обработчик прочих действий пагинатора и кнопок
@dp.callback_query_handler(lambda c: True)
async def process_callback_button2(callback_query: types.CallbackQuery):
    data = callback_query.data.split(':')
    action = data[0]

    if action == 'trip':
        trip = data[1]
        await bot.send_message(callback_query.from_user.id, f"Выбрана командировка {trip}\nДата создания: 01.01.2022", reply_markup=expenses_keyboard)
    elif action == 'prev_trips_page' or action == 'next_trips_page':
        current_page = int(data[1])
        trips = generate_business_trips()
        await display_business_trips(callback_query.from_user.id, trips, current_page)
    elif action == 'back_to_trips':
        trips = generate_business_trips()
        await display_business_trips(callback_query.from_user.id, trips, current_page=0)

    await bot.answer_callback_query(callback_query.id)

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
