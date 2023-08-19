import logging
import asyncio
from Forms import UserForm
from aiogram import Bot, Dispatcher, types, exceptions
from aiogram.types.chat_permissions import ChatPermissions
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup


API_TOKEN = '6279505625:AAF8u3JsaNXAuMtzqLmw2taUllw7zv1N2s4'
CHAT_ID = '-993911738'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)



async def start_cmd_handler(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        user = member.user
        if member.status in ["administrator", "creator", "member"]:
            # Если пользователь состоит в чате
            await bot.send_message(user_id, "Привет! Давай начнем использование бота!")
            # Тут можно добавить логику для команды /start
        else:
            # Если пользователь не состоит в чате
            await bot.send_message(user_id, f"{user.first_name}, вступите в чат, чтобы пользоваться ботом!")
    except exceptions.ChatNotFound:
        await bot.send_message(user_id, "Чат не найден!")


# Обработка команды /start
@dp.message_handler(commands=["contin"])
async def start(message: types.Message):
    user_id = message.from_user.id
    await start_cmd_handler(CHAT_ID, user_id)
    """
    Отправляет приветственное сообщение и переводит пользователя в состояние ожидания ввода имени
    """
    await message.answer(
        "Привет! Я могу запомнить твое ФИО, чтобы ты мог создать свой личный кабинет. Назови мне свое имя."
    )
    print('Do user form')
    await UserForm.waiting_for_name.set()
    print('Past user form')
async def on_shutdown(dp):
    logging.warning('Bot is shutting down. Goodbye!')

# Обработка ввода имени
@dp.message_handler(state=UserForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Сохраняет введенное имя, переводит пользователя в состояние ожидания ввода фамилии
    """
    async with state.proxy() as data:
        data["name"] = message.text

    await message.answer("Отлично! А теперь напиши свою фамилию.")
    await UserForm.waiting_for_surname.set()

# Обработка ввода фамилии
@dp.message_handler(Text(equals="Отмена", ignore_case=True), state=UserForm.waiting_for_surname)
@dp.message_handler(state=UserForm.waiting_for_surname)
async def process_surname(message: types.Message, state: FSMContext):
    """
    Сохраняет введенную фамилию, переводит пользователя в состояние ожидания ввода отчества
    """
    if message.text == "Отмена":
        await state.finish()
        return

    async with state.proxy() as data:
        data["surname"] = message.text

    await message.answer("Отлично! А теперь напиши свое отчество.")
    await UserForm.waiting_for_patronymic.set()

# Обработка ввода отчества
@dp.message_handler(Text(equals="Отмена", ignore_case=True), state=UserForm.waiting_for_patronymic)
@dp.message_handler(state=UserForm.waiting_for_patronymic)
async def process_patronymic(message: types.Message, state: FSMContext):
    """
    Сохраняет введенное отчество, создает личный кабинет пользователя и предлагает две кнопки: редактировать профиль и просмотреть профиль
    """
    if message.text == "Отмена":
        await state.finish()
        return

    async with state.proxy() as data:
        data["patronymic"] = message.text
        # Создание личного кабинета пользователя и отправка сообщения с кнопками
        profile_keyboard = types.InlineKeyboardMarkup()
        edit_profile_button = types.InlineKeyboardButton(
            "Редактировать профиль", callback_data="edit_profile"
        )
        view_profile_button = types.InlineKeyboardButton(
            "Посмотреть профиль", callback_data="view_profile"
        )
        profile_keyboard.row(edit_profile_button, view_profile_button)

        await message.answer(
            f"Успешно! Твои данные: <b>{data['surname']} {data['name']} {data['patronymic']}</b>.",
            reply_markup=profile_keyboard,
            parse_mode=ParseMode.HTML,
        )

    await state.finish()

# Обработка выбора кнопки в личном кабинете
@dp.callback_query_handler(text_contains="edit_profile")
async def edit_profile(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, "Ты нажал на кнопку 'Редактировать профиль'."
    )

@dp.callback_query_handler(text_contains="view_profile")
async def view_profile(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, "Ты нажал на кнопку 'Просмотреть профиль'."
    )

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = message.from_user
    await start_cmd_handler(CHAT_ID, user.id)

if __name__ == '__main__':


    # Запуск бота
    executor.start_polling(dp, on_shutdown=on_shutdown)
