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
        KeyboardButton(text="Завершить командировку"),
        KeyboardButton(text="Добавить расходы"),
        KeyboardButton(text="Как пользоваться")
    ]
    keyboard.add(*buttons)
    await message.answer("Выберите действие:", reply_markup=keyboard)


# добавлено: обработчик кнопки "Добавить расходы"
@dp.message_handler(text=['Добавить расходы'])
async def process_add_expense(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        KeyboardButton(text="Билеты"),
        KeyboardButton(text="Проживание"),
        KeyboardButton(text="Представительские расходы"),
        KeyboardButton(text="Назад")
    ]
    keyboard.add(*buttons)
    await message.answer("Выберите тип расходов:", reply_markup=keyboard)


# добавлено: обработчик кнопки "Завершить командировку"
@dp.message_handler(text=['Завершить командировку'])
async def process_finish_travel(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        # вместо примера списка командировок, добавьте свою логику
        KeyboardButton(text="Командировка 1"),
        KeyboardButton(text="Командировка 2"),
        KeyboardButton(text="Назад")
    ]
    keyboard.add(*buttons)
    await message.answer("Выберите командировку для завершения:", reply_markup=keyboard)


# обработчик команды "Новая командировка"
@dp.message_handler(lambda message: message.text == "Новая командировка", state=None)
async def new_travel_handler(message: types.Message):
    await message.answer("Введите название города, в который отправляетесь")
    await NewTravel.waiting_for_city.set()


# обработка ответа на запрос города
@dp.message_handler(state=NewTravel.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text
    await message.answer("Когда вы отправляетесь в командировку? (введите дату в формате ДД.ММ.ГГГГ)")
    await NewTravel.next()


# обработка ответа на запрос даты
@dp.message_handler(state=NewTravel.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = message.text
        # вместо простого вывода информации, вы можете добавить логику создания новой командировки с использованием данных из состояния
        text = f"Вы добавили новую командировку в {data['city']} на {data['date']}"
    await message.answer(text)
    await state.finish()


# добавлено: обработчик кнопки "Назад"
@dp.message_handler(text=['Назад'])
async def process_back(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        KeyboardButton(text="Мои командировки"),
        KeyboardButton(text="Новая командировка"),
        KeyboardButton(text="Завершить командировку"),
        KeyboardButton(text="Добавить расходы"),
        KeyboardButton(text="Как пользоваться")
    ]
    keyboard.add(*buttons)
    await message.answer("Главное меню:", reply_markup=keyboard)


# обработчик команды "Мои командировки"
@dp.message_handler(lambda message: message.text == "Мои командировки")
async def list_travels(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        KeyboardButton(text="Назад")
    ]
    keyboard.add(*buttons)
    # вместо простого вывода информации, вы можете добавить логику отображения списка командировок из вашей базы данных
    await message.answer("Список ваших командировок:", reply_markup=keyboard)


# добавлено: обработчик команды "Как пользоваться"
@dp.message_handler(lambda message: message.text == "Как пользоваться")
async def help(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    buttons = [
        KeyboardButton(text="Назад")
    ]
    keyboard.add(*buttons)

    text = """
    Для создания новой командировки введите "Новая командировка" и следуйте инструкциям.
    Для просмотра списка своих командировок введите "Мои командировки".
    Для завершения командировки выберите соответствующий пункт в меню.
    Для добавления расходов выберите соответствующий пункт в меню.
    """

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


# запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling())
