import logging
import asyncio
from aiogram import Bot, Dispatcher, types, exceptions
from aiogram.types.chat_permissions import ChatPermissions
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode


API_TOKEN = '6279505625:AAF8u3JsaNXAuMtzqLmw2taUllw7zv1N2s4'
CHAT_ID = '-993911738'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def start_cmd_handler(message: types.Message):
    user = message.from_user
    try:
        member = await bot.get_chat_member(CHAT_ID, user.id)
        if member.status in ["administrator", "creator", "member"]:
            # Если пользователь состоит в чате
            await message.answer("Привет! Давай начнем использование бота!")
            # Тут можно добавить логику для команды /start
        else:
            # Если пользователь не состоит в чате
            await bot.send_message(user.id, f"{user.first_name}, вступите в чат, чтобы пользоваться ботом!")
    except exceptions.ChatNotFound:
        await message.answer("Чат не найден!")


async def on_shutdown(dp):
    logging.warning('Bot is shutting down. Goodbye!')


if __name__ == '__main__':
    # Регистрация хендлеров
    dp.register_message_handler(start_cmd_handler, commands=["start"])

    # Запуск бота
    executor.start_polling(dp, on_shutdown=on_shutdown)
