import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton

# создание объекта бота
bot = Bot(token='6279505625:AAF8u3JsaNXAuMtzqLmw2taUllw7zv1N2s4')

# создание диспетчера
dp = Dispatcher(bot, storage=MemoryStorage())

# создание класса-состояния для хранения состояния при обработке команды "Новая командировка"
class NewTravel(StatesGroup):
    waiting_for_city = State()
    waiting_for_date = State()

# обработчик команды /start
@dp.message_handler(commands='start')
async def process_start_command(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        KeyboardButton(text="Мои командировки"),
        KeyboardButton(text="Новая командировка"),
        KeyboardButton(text="Как это работает")
    ]
    keyboard.add(*buttons)
    await message.answer("Выберите действие:", reply_markup=keyboard)

# обработчик кнопки "Мои командировки"
@dp.message_handler(text=['Мои командировки'])
async def process_my_travels(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        KeyboardButton(text="Добавить статью расходов"),
        KeyboardButton(text="Завершить командировку")
    ]
    keyboard.add(*buttons)
    await message.answer("Список командировок:", reply_markup=keyboard)

# обработчик кнопки "Новая командировка"
@dp.message_handler(text=['Новая командировка'])
async def process_new_travel(message: types.Message):
    await message.answer("Введите город:")
    await NewTravel.waiting_for_city.set()

# обработчик ввода города
@dp.message_handler(state=NewTravel.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text
    await message.answer("Введите дату начала в формате ДД.ММ.ГГГГ:")
    await NewTravel.waiting_for_date.set()

# обработчик ввода даты
@dp.message_handler(state=NewTravel.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = message.text
    await state.finish()
    await message.answer("Новая командировка создана!")
    # здесь можно добавить код для сохранения новой командировки в базу данных

# запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling())
