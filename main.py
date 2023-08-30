import asyncio
import logging
import random

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

bot = Bot(token='6584652808:AAGdp1-TcXf9RkHiiF9Fuji9w3c46do67Vo')
dp = Dispatcher(bot)

# Главное меню
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
button1 = KeyboardButton('Мои командировки')
button2 = KeyboardButton('Добавить расходы')
button3 = KeyboardButton('Новая командировка')
button4 = KeyboardButton('Завершить командировку')
button5 = KeyboardButton('Как пользоваться')
main_keyboard.add(button1, button2, button3, button4, button5)

# Клавиатура для выбора статьи расходов
expenses_keyboard = InlineKeyboardMarkup()
expenses_keyboard.add(InlineKeyboardButton(text="Билеты", callback_data="tickets"),
                      InlineKeyboardButton(text="Проживание", callback_data="accommodation"),
                      InlineKeyboardButton(text="Представительские расходы", callback_data="entertainment"),
                      InlineKeyboardButton(text="Назад", callback_data="main_menu"))

# Клавиатура для списка командировок
def generate_business_trips():
    # генерируем список командировок
    trips = ['Командировка {}'.format(i) for i in range(1, 6)]
    random.shuffle(trips)
    return trips

def construct_business_trips_keyboard(trips):
    keyboard = InlineKeyboardMarkup()
    for trip in trips:
        keyboard.add(InlineKeyboardButton(text=trip, callback_data=trip),)
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return keyboard

@dp.message_handler(commands=['start'])
async def start_message_handler(message: types.Message):
    await bot.send_message(message.chat.id, "Выберите действие из предложенного списка:", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text not in [button1.text, button2.text, button3.text, button4.text, button5.text], content_types=types.ContentType.TEXT)
async def text_message_handler(message: types.Message):
    await bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите действие из предложенного списка:", reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text in [button1.text, button2.text, button3.text, button4.text, button5.text], content_types=types.ContentType.TEXT)
async def menu_buttons_handler(message: types.Message):
    if message.text == button1.text:
        trips = generate_business_trips()
        await bot.send_message(message.chat.id, "Выберите командировку:", reply_markup=construct_business_trips_keyboard(trips))
    elif message.text == button2.text:
        await bot.send_message(message.chat.id, "Выберите статью расходов:", reply_markup=expenses_keyboard)
    elif message.text == button3.text:
        await bot.send_message(message.chat.id, "Введите город и дату начала командировки:")
    elif message.text == button4.text:
        # Здесь должна быть логика завершения командировки
        trips = generate_business_trips()
        await bot.send_message(message.chat.id, "Выберите командировку для завершения:", reply_markup=construct_business_trips_keyboard(trips))
    elif message.text == button5.text:
        # Здесь должны быть инструкции по использованию
        await bot.send_message(message.chat.id, "Как пользоваться ботом?", reply_markup=main_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Выберите действие из предложенного списка:", reply_markup=main_keyboard)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: True)
async def process_callback_button2(callback_query: types.CallbackQuery):
    trip = callback_query.data
    await bot.send_message(callback_query.from_user.id, f"Выбрана командировка {trip}")
    await bot.answer_callback_query(callback_query.id)

async def main():
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
