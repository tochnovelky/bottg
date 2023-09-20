import os
import re
from datetime import datetime

from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from bot import dp, bot
from functions import display_business_trips, date_in_trip_name, generate_paginator, objects_list_to_ids_list, \
    display_expenses, enter_expense_create_pdf, from_photo_to_pdf, delete_single_pdf, create_new_expense, \
    name_generator, merge_pdfs
from middleware_aiogram import *
from models.classes import BusinessTrip, Expense

open_trips = {}

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
trips_button = KeyboardButton('Мои командировки')
add_expenses_button = KeyboardButton('Добавить расходы')
new_trip_button = KeyboardButton('Новая командировка')
close_trip_button = KeyboardButton('Завершить командировку')
how_use_button = KeyboardButton('Как пользоваться')
main_keyboard.add(trips_button, add_expenses_button, new_trip_button, close_trip_button, how_use_button)

expenses_buttons = [InlineKeyboardButton(text="Билеты", callback_data="tickets"),
                    InlineKeyboardButton(text="Проживание", callback_data="accommodation"),
                    InlineKeyboardButton(text="Предст. расходы", callback_data="entertainment"),
                    InlineKeyboardButton(text="Связь", callback_data="telecom_service"),
                    InlineKeyboardButton(text="Такси", callback_data="taxi_service"),
                    InlineKeyboardButton(text="Платный проезд", callback_data="paid_transport"),
                    InlineKeyboardButton(text="Прочее", callback_data="other")]

expenses_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
for button in expenses_buttons:
    expenses_keyboard.row(button)

cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cancel_button = KeyboardButton('Отмена')
cancel_keyboard.add(cancel_button)

question_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
yes_button = KeyboardButton('Да')
no_button = KeyboardButton('Нет')
cancel_button = KeyboardButton('Отмена')
question_keyboard.row(yes_button, no_button)
question_keyboard.row(cancel_button)

receipt_question_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
electro_button = KeyboardButton('Электронный')
fis_button = KeyboardButton('Физический')
cancel_button = KeyboardButton('Отмена')
receipt_question_keyboard.row(electro_button, fis_button)
receipt_question_keyboard.row(cancel_button)

expense_category = {"tickets": "Билеты", "accommodation": "Проживание", "entertainment": "Предст. расходы",
                    "telecom_service": "Связь", "taxi_service": "Такси", "paid_transport": "Платный проезд",
                    "other": "Прочее"}


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_message_handler(message: types.Message, state: FSMContext):
    if not await user_in_db(message.from_user.id):
        keyboard = types.ReplyKeyboardRemove()
        await state.set_state(UserRegistration.waiting_for_fullname.state)
        await message.answer("Регистрация.\nВведите ФИО:)",
                             reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id, "Выберете команду из меню", reply_markup=main_keyboard)


class AddNewExpense(StatesGroup):
    waiting_for_expense_category = State()
    waiting_for_amount = State()
    waiting_for_comment = State()
    waiting_for_photo = State()
    waiting_for_answer = State()
    waiting_for_trip = State()


class AddNewTrip(StatesGroup):
    waiting_for_date = State()
    waiting_for_country = State()


class TripsMenu(StatesGroup):
    waiting_for_trip = State()
    waiting_for_expense = State()
    detail_expense = State()


class UserRegistration(StatesGroup):
    waiting_for_fullname = State()
    waiting_for_position = State()


class AddNewExpenseEntertainment(StatesGroup):
    waiting_for_answer_trip = State()
    waiting_for_trip = State()
    waiting_for_date = State()
    waiting_for_place = State()
    waiting_for_purpose = State()
    waiting_for_members = State()
    waiting_for_result = State()
    waiting_for_amount = State()
    waiting_for_answer_receipt = State()
    waiting_for_receipt = State()
    waiting_for_receipt_number = State()

class AddNewExpenseTaxi(StatesGroup):
    waiting_for_answer_trip = State()
    waiting_for_trip = State()
    waiting_for_date = State()
    waiting_for_place = State()
    waiting_for_were = State()
    waiting_for_were_from = State()
    waiting_for_purpose= State()
    waiting_for_amount = State()
    waiting_for_answer_receipt = State()
    waiting_for_receipt = State()
    waiting_for_screenshot = State()

# Обработчик сообщений об отмене
@dp.message_handler(commands=["cancel"], state='*')
@dp.message_handler(Text(equals="Отмена", ignore_case=True), state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=main_keyboard)


# ======================================================================================================================
# Обработчик кнопок главного меню
@dp.message_handler(
    lambda message: message.text in [trips_button.text, add_expenses_button.text, new_trip_button.text,
                                     close_trip_button.text, how_use_button.text],
    content_types=types.ContentType.TEXT)
async def menu_buttons_handler(message: types.Message, state: FSMContext):
    if message.text == trips_button.text:
        trips = session.query(BusinessTrip).filter_by(user_id=message.from_user.id).all()
        if not trips:
            await bot.send_message(message.chat.id, "У вас нет командировок.", reply_markup=main_keyboard)
            return

        await state.set_state(TripsMenu.waiting_for_trip.state)
        await state.update_data(trips=trips)
        await display_business_trips(message.chat.id, trips, current_page=0)

    elif message.text == add_expenses_button.text:
        await state.set_state(AddNewExpense.waiting_for_expense_category.state)
        await bot.send_message(message.chat.id, "Выберите одну из статей расходов", reply_markup=cancel_keyboard)
        await bot.send_message(message.chat.id, "Список статей расходов:", reply_markup=expenses_keyboard)

    elif message.text == new_trip_button.text:
        await state.set_state(AddNewTrip.waiting_for_date.state)
        await bot.send_message(message.chat.id,
                               "Создание новой командировки.\nУкажите дату начала командировки в формате ДД.ММ.ГГГГ:",
                               reply_markup=cancel_keyboard)


    elif message.text == how_use_button.text:
        await bot.send_message(message.chat.id, "Как пользоваться ботом?", reply_markup=main_keyboard)


# ======================================================================================================================
# ДОБАВИТЬ РАСХОДЫ

# Обработчик callback_query запросов от меню с расходами
@dp.callback_query_handler(state=AddNewExpense.waiting_for_expense_category)
async def expense_chosen_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data not in ["tickets", "accommodation", "entertainment", "telecom_service", "taxi_service",
                                   "paid_transport", "other"]:
        await bot.send_message(callback_query.message.chat.id, "Выберите статью расходов:")
        return

    elif callback_query.data == 'entertainment':
        await bot.answer_callback_query(callback_query.id)
        expense = expense_category[callback_query.data]
        await state.update_data(expense=expense)
        await state.update_data(additional_list=[])
        await state.set_state(AddNewExpenseEntertainment.waiting_for_answer_trip.state)
        await bot.send_message(callback_query.message.chat.id,
                               f"Статья расхода: {expense}\n\nДобавить расход в командировку?",
                               reply_markup=question_keyboard)
    elif callback_query.data == 'taxi_service':
        await bot.answer_callback_query(callback_query.id)
        expense = expense_category[callback_query.data]
        await state.update_data(expense=expense)
        await state.update_data(additional_list=[])
        await state.set_state(AddNewExpenseTaxi.waiting_for_answer_trip.state)
        await bot.send_message(callback_query.message.chat.id,
                               f"Статья расхода: {expense}\n\nДобавить расход в командировку?",
                               reply_markup=question_keyboard)

@dp.message_handler(content_types=types.ContentType.TEXT, state=AddNewExpenseEntertainment.waiting_for_answer_trip)
async def entertainment_trip_message(message: types.Message, state: FSMContext):
    trips = session.query(BusinessTrip).filter_by(user_id=message.from_user.id).all()

    if message.text in ['Да', 'да']:
        if not trips:
            await state.update_data(chosen_trip_name='Не указана')
            await state.set_state(AddNewExpenseEntertainment.waiting_for_date.state)
            await bot.send_message(message.chat.id,
                                   f"У вас нет командировок.\nПосле завершения добавления расхода, отчет в формате PDF сформируется и отправится в чат.\n\nВведите дату расхода в формате ДД.ММ.ГГГГ:",
                                   reply_markup=cancel_keyboard)

        else:
            trips_ids = objects_list_to_ids_list(trips)
            await state.update_data(trips_ids=trips_ids)
            await display_business_trips(message.chat.id, trips, current_page=0)
            await state.set_state(AddNewExpenseEntertainment.waiting_for_trip.state)

    elif message.text in ['Нет', 'нет']:
        await state.update_data(chosen_trip_name='Не указана')
        await state.set_state(AddNewExpenseEntertainment.waiting_for_date.state)
        await bot.send_message(message.chat.id,
                               f"\nВведите дату расхода в формате ДД.ММ.ГГГГ:",
                               reply_markup=cancel_keyboard)
@dp.message_handler(content_types=types.ContentType.TEXT, state=AddNewExpenseTaxi.waiting_for_answer_trip)
async def taxi_trip_message(message: types.Message, state: FSMContext):
    trips = session.query(BusinessTrip).filter_by(user_id=message.from_user.id).all()

    if message.text in ['Да', 'да']:
        if not trips:
            await state.update_data(chosen_trip_name='Не указана')
            await state.set_state(AddNewExpenseTaxi.waiting_for_date.state)
            await bot.send_message(message.chat.id,
                                   f"У вас нет командировок.\nПосле завершения добавления расхода, отчет в формате PDF сформируется и отправится в чат.\n\nВведите дату расхода в формате ДД.ММ.ГГГГ:",
                                   reply_markup=cancel_keyboard)

        else:
            trips_ids = objects_list_to_ids_list(trips)
            await state.update_data(trips_ids=trips_ids)
            await display_business_trips(message.chat.id, trips, current_page=0)
            await state.set_state(AddNewExpenseTaxi.waiting_for_trip.state)

    elif message.text in ['Нет', 'нет']:
        await state.update_data(chosen_trip_name='Не указана')
        await state.set_state(AddNewExpenseTaxi.waiting_for_date.state)
        await bot.send_message(message.chat.id,
                               f"\nВведите дату расхода в формате ДД.ММ.ГГГГ:",
                               reply_markup=cancel_keyboard)
@dp.callback_query_handler(lambda c: c.data.startswith('id:'), state=AddNewExpenseTaxi.waiting_for_trip)
async def taxi_trip_added_message(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    trips_ids = data.get('trips_ids')
    trip_id = str(callback_query.data.split(':')[1])

    await bot.answer_callback_query(callback_query.id)

    if trip_id not in trips_ids:
        await bot.send_message(callback_query.message.chat.id, "Такой командировки не найдено(")
    else:
        chosen_trip_name = session.query(BusinessTrip).filter_by(id=int(trip_id)).first()
        chosen_trip_name = chosen_trip_name.name
        await state.update_data(chosen_trip_id=trip_id)
        await state.update_data(chosen_trip_name=chosen_trip_name)
        await state.set_state(AddNewExpenseTaxi.waiting_for_date.state)
        await bot.send_message(callback_query.message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nВведите дату в формате ДД.ММ.ГГГГ:")

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_date, content_types=types.ContentType.TEXT)
async def taxi_date_message(message: types.Message, state: FSMContext):
    date_pattern = r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.\d{4}$'
    if not re.match(date_pattern, message.text):
        await bot.send_message(message.chat.id, "Создание новой командировки.\nПожалуйста, введите дату в формате "
                                                "ДД.ММ.ГГГГ:")
        return
    data = await state.get_data()
    expense = data.get('expense')
    chosen_trip_name = data.get('chosen_trip_name')
    await state.update_data(date=message.text)
    await state.set_state(AddNewExpenseTaxi.waiting_for_place.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {message.text}\n\nУкажите место:")


@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_place, content_types=types.ContentType.TEXT)
async def taxi_place_message(message: types.Message, state: FSMContext):
    await state.update_data(place=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    chosen_trip_name = data.get('chosen_trip_name')

    await state.set_state(AddNewExpenseTaxi.waiting_for_were.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {message.text}\n\nОткуда вы ехали?:")

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_were, content_types=types.ContentType.TEXT)
async def taxi_were_message(message: types.Message, state: FSMContext):
    await state.update_data(were=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_were_from.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда: {message.text}\n\nОткуда:")

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_were_from, content_types=types.ContentType.TEXT)
async def taxi_were_from_message(message: types.Message, state: FSMContext):
    await state.update_data(were_from=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')

    await state.set_state(AddNewExpenseTaxi.waiting_for_purpose.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда: {were}\n\nОткуда:{message.text}\n\n Цель поездки:")

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_purpose, content_types=types.ContentType.TEXT)
async def taxi_purpose_message(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from=data.get('were_from')
    await state.set_state(AddNewExpenseTaxi.waiting_for_amount.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{message.text}")

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_answer_receipt, content_types=types.ContentType.TEXT)
async def taxi_amount_message(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from=data.get('were_from')
    purpose = data.get('purpose')


    await state.set_state(AddNewExpenseTaxi.waiting_for_amount.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}n\n\ Прикрепите фото чека: ")



@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_answer_receipt, content_types=types.ContentType.TEXT)
async def taxi_answer_receipt_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from = data.get('were_from')
    purpose = data.get('purpose')
    amount = data.get('amount')

    if message.text in ['Физический', 'физический']:
        await state.set_state(AddNewExpenseTaxi.waiting_for_receipt_number.state)

        await bot.send_message(message.chat.id,
                                f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nПришлите фото поездки :",
                               reply_markup=cancel_keyboard)
    if message.text in ['Электронный', 'электронный']:
        await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt.state)
        await bot.send_message(message.chat.id,
                                f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}n\n\ \n\nПрикрепите фото чека или файл в формате PDF:",
                               reply_markup=cancel_keyboard)

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_receipt,
                    content_types=[types.ContentType.PHOTO])
async def taxi_photo_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from = data.get('were_from')
    purpose = data.get('purpose')
    amount = data.get('amount')

    await message.answer("Вы отправили фотографию!")
    name = name_generator()
    name_pdf = name_generator()
    # Добавили имя доп файла (бывшего фото) в список с названиями всех остальных таких файлов
    additional_list.append(name_pdf)
    await state.update_data(additional_list=additional_list)

    await message.photo[-1].download(destination_file=f'photo_files/{name}.jpeg')

    from_photo_to_pdf(image_path=f'photo_files/{name}.jpeg', pdf_path=f'pdf_files/{name_pdf}.pdf')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt_number.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nПришлите фото поездки :",
                               reply_markup=cancel_keyboard)

@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_receipt, content_types=[types.ContentType.DOCUMENT])
async def taxi_file_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from = data.get('were_from')
    purpose = data.get('purpose')
    amount = data.get('amount')


    print('message.document.mime_type')
    print(message.document.mime_type)

    if message.document.mime_type == 'application/pdf':
        await message.answer("Вы отправили PDF файл!")
        # Если это PDF-файл, сохраняем его в папке pdf_files
        file_id = message.document.file_id
        file_path = await bot.get_file(file_id)
        file_name = name_generator()
        await file_path.download(os.path.join('pdf_files', f'{file_name}.pdf'))

        additional_list.append(file_name)
        await state.update_data(additional_list=additional_list)

        await state.set_state(AddNewExpenseTaxi.waiting_for_screenshot.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nПришлите фото поездки :",
                               reply_markup=cancel_keyboard)
    elif message.document.mime_type in ['image/png', 'image/jpeg']:
        await message.answer("Вы отправили фотографию как файл!")
        name = name_generator()
        name_pdf = name_generator()
        file_id = message.document.file_id
        file_path = await bot.get_file(file_id)
        await file_path.download(os.path.join('photo_files', f'{name}.jpeg'))

        from_photo_to_pdf(image_path=f'photo_files/{name}.jpeg', pdf_path=f'pdf_files/{name_pdf}.pdf')

        # Добавили имя доп файла (бывшего фото) в список с названиями всех остальных таких файлов
        additional_list.append(name_pdf)
        await state.update_data(additional_list=additional_list)

        await state.set_state(AddNewExpenseTaxi.waiting_for_screenshot.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nЧек прикреплен n\nПришлите фото поездки :",
                               reply_markup=cancel_keyboard)

    else:
        await bot.send_message(message.chat.id, 'Прикрепите фото в формате JPEG или PNG или файл PDF:')


@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_screenshot,
                    content_types=[types.ContentType.PHOTO])
async def taxi_screenshot_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from = data.get('were_from')
    purpose = data.get('purpose')
    amount = data.get('amount')

    await message.answer("Вы отправили фотографию!")
    name = name_generator()
    name_pdf = name_generator()
    # Добавили имя доп файла (бывшего фото) в список с названиями всех остальных таких файлов
    additional_list.append(name_pdf)
    await state.update_data(additional_list=additional_list)

    await message.photo[-1].download(destination_file=f'photo_files/{name}.jpeg')

    from_photo_to_pdf(image_path=f'photo_files/{name}.jpeg', pdf_path=f'pdf_files/{name_pdf}.pdf')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_screenshot.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nПришлите фото поездки :",
                               reply_markup=cancel_keyboard)


@dp.message_handler(state=AddNewExpenseTaxi.waiting_for_screenshot, content_types=[types.ContentType.DOCUMENT])
async def taxi_filescreenshot_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')
    were = data.get('were')
    were_from = data.get('were_from')
    purpose = data.get('purpose')
    amount = data.get('amount')

    print('message.document.mime_type')
    print(message.document.mime_type)

    if message.document.mime_type == 'application/pdf':
        await message.answer("Вы отправили PDF файл!")
        # Если это PDF-файл, сохраняем его в папке pdf_files
        file_id = message.document.file_id
        file_path = await bot.get_file(file_id)
        file_name = name_generator()
        await file_path.download(os.path.join('pdf_files', f'{file_name}.pdf'))

        additional_list.append(file_name)
        await state.update_data(additional_list=additional_list)

        await state.set_state(AddNewExpenseTaxi.waiting_for_screenshot.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nПришлите фото поездки :",
                               reply_markup=cancel_keyboard)
    elif message.document.mime_type in ['image/png', 'image/jpeg']:
        await message.answer("Вы отправили фотографию как файл!")
        name = name_generator()
        name_pdf = name_generator()
        file_id = message.document.file_id
        file_path = await bot.get_file(file_id)
        await file_path.download(os.path.join('photo_files', f'{name}.jpeg'))

        from_photo_to_pdf(image_path=f'photo_files/{name}.jpeg', pdf_path=f'pdf_files/{name_pdf}.pdf')

        # Добавили имя доп файла (бывшего фото) в список с названиями всех остальных таких файлов
        additional_list.append(name_pdf)
        await state.update_data(additional_list=additional_list)

        await state.set_state(AddNewExpenseTaxi.waiting_for_screenshot.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nКуда?: {were}\n\nОткуда:{were_from}\n\n Цель поездки:{purpose}\n\nФото аоездки прикреплено",
                               reply_markup=cancel_keyboard)

    else:
        await bot.send_message(message.chat.id, 'Прикрепите фото в формате JPEG или PNG или файл PDF:')



@dp.callback_query_handler(lambda c: c.data.startswith('id:'), state=AddNewExpenseEntertainment.waiting_for_trip)
async def entertainment_trip_added_message(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    trips_ids = data.get('trips_ids')
    trip_id = str(callback_query.data.split(':')[1])

    await bot.answer_callback_query(callback_query.id)

    if trip_id not in trips_ids:
        await bot.send_message(callback_query.message.chat.id, "Такой командировки не найдено(")
    else:
        chosen_trip_name = session.query(BusinessTrip).filter_by(id=int(trip_id)).first()
        chosen_trip_name = chosen_trip_name.name
        await state.update_data(chosen_trip_id=trip_id)
        await state.update_data(chosen_trip_name=chosen_trip_name)
        await state.set_state(AddNewExpenseEntertainment.waiting_for_date.state)
        await bot.send_message(callback_query.message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nВведите дату в формате ДД.ММ.ГГГГ:")



@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_date, content_types=types.ContentType.TEXT)
async def entertainment_date_message(message: types.Message, state: FSMContext):
    date_pattern = r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.\d{4}$'
    if not re.match(date_pattern, message.text):
        await bot.send_message(message.chat.id, "Создание новой командировки.\nПожалуйста, введите дату в формате "
                                                "ДД.ММ.ГГГГ:")
        return
    data = await state.get_data()
    expense = data.get('expense')
    chosen_trip_name = data.get('chosen_trip_name')
    await state.update_data(date=message.text)
    await state.set_state(AddNewExpenseEntertainment.waiting_for_place.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {message.text}\n\nУкажите место:")


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_place, content_types=types.ContentType.TEXT)
async def entertainment_place_message(message: types.Message, state: FSMContext):
    await state.update_data(place=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    chosen_trip_name = data.get('chosen_trip_name')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_purpose.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {message.text}\n\nВведите цель встречи:")


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_purpose, content_types=types.ContentType.TEXT)
async def entertainment_purpose_message(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    chosen_trip_name = data.get('chosen_trip_name')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_members.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nЦель встречи: {massage.text}\n\nУкажите участников встречи:")


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_members, content_types=types.ContentType.TEXT)
async def entertainment_members_message(message: types.Message, state: FSMContext):
    await state.update_data(members=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    purpose = data.get('purpose')
    chosen_trip_name = data.get('chosen_trip_name')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_result.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nЦель встречи: {purpose}\nУчастники:{message.text}\n\nУкажите результат встречи:")


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_result, content_types=types.ContentType.TEXT)
async def entertainment_result_message(message: types.Message, state: FSMContext):
    await state.update_data(result=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    purpose = data.get('purpose')
    chosen_trip_name = data.get('chosen_trip_name')
    members = data.get('members')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_amount.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {message.text}\n\nУкажите сумму:")


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_amount, content_types=types.ContentType.TEXT)
async def entertainment_amount_message(message: types.Message, state: FSMContext):
    amount = float(message.text)
    await state.update_data(amount=amount)
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    purpose = data.get('purpose')
    members = data.get('members')
    chosen_trip_name = data.get('chosen_trip_name')
    result = data.get('result')

    try:
        await state.set_state(AddNewExpenseEntertainment.waiting_for_answer_receipt.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\n\nДата: {date}\nМесто: {place}\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {result}\nСумма: {amount}\n\nУ вас электронный чек или физический?",
                               reply_markup=receipt_question_keyboard)
    except ValueError:
        await bot.send_message(message.chat.id, "Некорректное значение суммы. Введите число:")
        return


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_answer_receipt, content_types=types.ContentType.TEXT)
async def entertainment_answer_receipt_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    purpose = data.get('purpose')
    members = data.get('members')
    amount = data.get('amount')
    chosen_trip_name = data.get('chosen_trip_name')
    result = data.get('result')

    if message.text in ['Физический', 'физический']:
        await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt_number.state)

        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\nДата: {date}\nМесто: {place}"
                               f"\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {result}\nСумма: "
                               f"{amount}\n\nВведите номер чека:",
                               reply_markup=cancel_keyboard)
    if message.text in ['Электронный', 'электронный']:
        await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\nДата: {date}\nМесто: {place}"
                               f"\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {result}\nСумма: "
                               f"{amount}\n\nПрикрепите фото чека или файл в формате PDF:",
                               reply_markup=cancel_keyboard)



@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_receipt,
                    content_types=[types.ContentType.PHOTO])
async def entertainment_photo_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    purpose = data.get('purpose')
    members = data.get('members')
    amount = data.get('amount')
    chosen_trip_name = data.get('chosen_trip_name')
    result = data.get('result')
    additional_list = data.get('additional_list')

    await message.answer("Вы отправили фотографию!")
    name = name_generator()
    name_pdf = name_generator()
    # Добавили имя доп файла (бывшего фото) в список с названиями всех остальных таких файлов
    additional_list.append(name_pdf)
    await state.update_data(additional_list=additional_list)

    await message.photo[-1].download(destination_file=f'photo_files/{name}.jpeg')

    from_photo_to_pdf(image_path=f'photo_files/{name}.jpeg', pdf_path=f'pdf_files/{name_pdf}.pdf')

    await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt_number.state)
    await bot.send_message(message.chat.id,
                           f"Командировка: {chosen_trip_name}\nРасход: {expense}\nДата: {date}\nМесто: {place}"
                           f"\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {result}\nСумма: "
                           f"{amount}\nЧек прикреплен\n\nВведите номер чека:",
                           reply_markup=cancel_keyboard)


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_receipt, content_types=[types.ContentType.DOCUMENT])
async def entertainment_file_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expense = data.get('expense')
    date = data.get('date')
    place = data.get('place')
    purpose = data.get('purpose')
    members = data.get('members')
    amount = data.get('amount')
    chosen_trip_name = data.get('chosen_trip_name')
    result = data.get('result')
    additional_list = data.get('additional_list')

    print('message.document.mime_type')
    print(message.document.mime_type)

    if message.document.mime_type == 'application/pdf':
        await message.answer("Вы отправили PDF файл!")
        # Если это PDF-файл, сохраняем его в папке pdf_files
        file_id = message.document.file_id
        file_path = await bot.get_file(file_id)
        file_name = name_generator()
        await file_path.download(os.path.join('pdf_files', f'{file_name}.pdf'))

        additional_list.append(file_name)
        await state.update_data(additional_list=additional_list)

        await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt_number.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\nДата: {date}\nМесто: {place}"
                               f"\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {result}\nСумма: "
                               f"{amount}\nЧек прикреплен\n\nВведите номер чека:",
                               reply_markup=cancel_keyboard)

    elif message.document.mime_type in ['image/png', 'image/jpeg']:
        await message.answer("Вы отправили фотографию как файл!")
        name = name_generator()
        name_pdf = name_generator()
        file_id = message.document.file_id
        file_path = await bot.get_file(file_id)
        await file_path.download(os.path.join('photo_files', f'{name}.jpeg'))

        from_photo_to_pdf(image_path=f'photo_files/{name}.jpeg', pdf_path=f'pdf_files/{name_pdf}.pdf')

        # Добавили имя доп файла (бывшего фото) в список с названиями всех остальных таких файлов
        additional_list.append(name_pdf)
        await state.update_data(additional_list=additional_list)

        await state.set_state(AddNewExpenseEntertainment.waiting_for_receipt_number.state)
        await bot.send_message(message.chat.id,
                               f"Командировка: {chosen_trip_name}\nРасход: {expense}\nДата: {date}\nМесто: {place}"
                               f"\nЦель встречи: {purpose}\nУчастники:{members}\nРезультат встречи: {result}\nСумма: "
                               f"{amount}\nЧек прикреплен\n\nВведите номер чека:",
                               reply_markup=cancel_keyboard)

    else:
        await bot.send_message(message.chat.id, 'Прикрепите фото в формате JPEG или PNG или файл PDF:')


@dp.message_handler(state=AddNewExpenseEntertainment.waiting_for_receipt_number, content_types=types.ContentType.TEXT)
async def entertainment_receipt_number_message(message: types.Message, state: FSMContext):
    await state.update_data(receipt_number=message.text)
    data = await state.get_data()
    expense = data.get('expense')
    date_string = data.get('date')
    date_object = datetime.strptime(date_string, "%d.%m.%Y").date()
    place = data.get('place')
    purpose = data.get('purpose')
    members = data.get('members')
    amount = data.get('amount')
    chosen_trip_name = data.get('chosen_trip_name')
    result = data.get('result')
    chosen_trip_id = data.get('chosen_trip_id')
    receipt_number = data.get('receipt_number')

    if chosen_trip_name != 'Не указана':
        create_new_expense(message=message, amount=amount, expense=expense, date_object=date_object,
                           chosen_trip_id=chosen_trip_id)
        await bot.send_message(message.chat.id,
                               f"Расход {expense} успешно добавлен в командировку {chosen_trip_name}\n\nДата: {date_string}\nМесто: {place}\nЦель встречи: {purpose}\nУчастники: {members}\nРезультат встречи: {result}\nСумма: {amount}",
                               reply_markup=main_keyboard)
        await state.finish()

    else:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        user_fullname = user.full_name
        user_position = user.position

        report_pdf_name = enter_expense_create_pdf(date=date_string, place=place, purpose=purpose, members=members,
                                                   amount=amount, receipt_number=receipt_number,
                                                   user_fullname=user_fullname, user_position=user_position,
                                                   result=result)
        data = await state.get_data()
        additional_list = data.get('additional_list')

        for i in additional_list:
            merge_pdfs(report_pdf_name, i)  # Вызываем функцию объединения pdf файлов

        # Откройте и прочитайте PDF-файл
        with open(f'pdf_files/{report_pdf_name}.pdf', "rb") as pdf_file:
            # Отправьте файл пользователю с помощью метода send_document
            await bot.send_message(message.chat.id, 'Отчет формируется и скоро будет отправлен в чат!',
                                   reply_markup=main_keyboard)
            await bot.send_document(message.from_user.id, pdf_file,
                                    parse_mode=ParseMode.MARKDOWN)
        await state.finish()
        # delete_single_pdf(f'pdf_files/{report_pdf_name}.pdf')



# Обработчик message запросов в состоянии ожидания расхода
@dp.message_handler(state=AddNewExpense.waiting_for_expense_category, content_types=types.ContentType.TEXT)
async def expense_chosen_message(message: types.Message):
    await bot.send_message(message.chat.id, f"Пожалуйста, выберете статью расхода из меню",
                           reply_markup=expenses_keyboard)


# Обработчик message запросов в состоянии ожидания суммы
@dp.message_handler(state=AddNewExpense.waiting_for_amount, content_types=types.ContentType.TEXT)
async def amount_added(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(chosen_amount=amount)
        data = await state.get_data()
        expense = data.get("chosen_expense")
        await state.set_state(AddNewExpense.waiting_for_comment.state)
        await bot.send_message(message.chat.id,
                               f"Категория: {expense}\nСумма: {amount} руб.\nВведите комментарий:")

    except ValueError:
        await bot.send_message(message.chat.id, "Некорректное значение суммы. Введите число:")
        return


# Обработчик message запросов в состоянии ожидания коммента
@dp.message_handler(state=AddNewExpense.waiting_for_comment, content_types=types.ContentType.TEXT)
async def comment_added(message: types.Message, state: FSMContext):
    comment = message.text
    if not comment:
        await bot.send_message(message.chat.id, "Необходимо ввести комментарий:")

    await state.update_data(chosen_comment=comment)
    data = await state.get_data()
    expense = data.get("chosen_expense")
    amount = data.get("chosen_amount")
    await state.set_state(AddNewExpense.waiting_for_photo.state)
    await bot.send_message(message.chat.id,
                           f"Категория: {expense}\nСумма: {amount} руб.\nКомментарий: {comment}\n\nОтправьте фото:")


# Обработчик message запросов в состоянии ожидания фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddNewExpense.waiting_for_photo)
async def photo_added_photo(message: types.Message, state: FSMContext):
    # Тут будет сохраняться картинка и записываться путь к ней в БД

    await bot.send_message(message.chat.id, "Добавить данный расход в командировку?",
                           reply_markup=question_keyboard)
    # await message.photo[-1].download('test.jpg')
    await state.set_state(AddNewExpense.waiting_for_answer.state)


# Обработчик message запросов в состоянии ожидания фото, если пользователь вводит текст вместо фото
@dp.message_handler(state=AddNewExpense.waiting_for_photo, content_types=types.ContentType.TEXT)
async def photo_added_message(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, f"Пришлите фото чека:")


@dp.message_handler(content_types=types.ContentType.TEXT, state=AddNewExpense.waiting_for_answer)
async def question_added(message: types.Message, state: FSMContext):
    trips = session.query(BusinessTrip).filter_by(user_id=message.from_user.id).all()
    trips_ids = objects_list_to_ids_list(trips)
    await state.update_data(trips_ids=trips_ids)

    data = await state.get_data()
    amount = data.get('chosen_amount')
    expense = data.get('chosen_expense')
    comment = data.get('chosen_comment')

    if message.text in ['Да', 'да']:
        await display_business_trips(message.chat.id, trips, current_page=0)
        await state.set_state(AddNewExpense.waiting_for_trip.state)

    elif message.text in ['Нет', 'нет']:
        try:
            new_expense = Expense(amount=amount, category=expense, comment=comment, user_id=int(message.from_user.id))
            session.add(new_expense)
            session.commit()
            await bot.send_message(message.chat.id, f"Расход успешно добавлен. Отчет формируется.",
                                   reply_markup=main_keyboard)
            await state.finish()
        except Exception as e:
            await bot.send_message(message.chat.id, f"Произошла ошибка при записи данных в БД.\nError: {e}",
                                   reply_markup=main_keyboard)
            await state.finish()

    # тут вызываем функцию сохранения фото в папку
    # тут вызываем функцию записи пути к папке и всех остальных данных в БД


@dp.callback_query_handler(lambda c: c.data.startswith('id:'), state=AddNewExpense.waiting_for_trip)
async def trip_added(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    trips_ids = data.get("trips_ids")
    amount = data.get('chosen_amount')
    expense = data.get('chosen_expense')
    comment = data.get('chosen_comment')
    trip_id = str(callback_query.data.split(':')[1])
    await bot.answer_callback_query(callback_query.id)

    if trip_id not in trips_ids:
        await bot.send_message(callback_query.message.chat.id, "Такой командировки не найдено(")
    else:
        try:
            new_expense = Expense(amount=amount, category=expense, comment=comment, trip_id=int(trip_id))
            session.add(new_expense)
            session.commit()
            await bot.send_message(callback_query.message.chat.id, f"Расход успешно добавлен в командировку",
                                   reply_markup=main_keyboard)
            await state.finish()
        except Exception as e:
            await bot.send_message(callback_query.message.chat.id,
                                   f"Произошла ошибка при записи данных в БД.\nError: {e}")
            await state.finish()


@dp.message_handler(content_types=types.ContentType.TEXT, state=AddNewExpense.waiting_for_trip)
async def text_handler_while_in_menu(message: types.Message):
    await bot.send_message(message.chat.id, "Пожалуйста, выберете командировку из меню.")


# ======================================================================================================================
# НОВАЯ КОМАНДИРОВКА

# Обработчик message запросов в состоянии ожидания фото, если пользователь вводит текст вместо фото
@dp.message_handler(state=AddNewTrip.waiting_for_date, content_types=types.ContentType.TEXT)
async def date_chosen_message(message: types.Message, state: FSMContext):
    date_pattern = r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.\d{4}$'
    if not re.match(date_pattern, message.text):
        await bot.send_message(message.chat.id, "Создание новой командировки.\nПожалуйста, введите дату в формате "
                                                "ДД.ММ.ГГГГ:")
        return

    await state.update_data(chosen_date=message.text)
    await state.set_state(AddNewTrip.waiting_for_country.state)
    await bot.send_message(message.chat.id,
                           f"Создание новой командировки.\nДата начала: {message.text}\nУкажите страну:")


@dp.message_handler(state=AddNewTrip.waiting_for_country, content_types=types.ContentType.TEXT)
async def country_chosen_message(message: types.Message, state: FSMContext):
    country_pattern = r'\d+'
    if bool(re.search(country_pattern, message.text)):
        await bot.send_message(message.chat.id, "Пожалуйста, введите название страны:")
        return

    await state.update_data(chosen_country=message.text)
    data = await state.get_data()
    start_date_string = data.get("chosen_date")
    start_date_object = datetime.strptime(start_date_string, "%d.%m.%Y").date()
    name = date_in_trip_name(start_date_string)  # Тут вызываем функцию для генерации названия командировки из даты

    # Тут вызываем функцию для записи в БД: Имя командировки, Дату начала, Страну
    try:
        new_trip = BusinessTrip(name=name, start_date=start_date_object, country=message.text,
                                user_id=message.from_user.id)
        session.add(new_trip)
        session.commit()
        await bot.send_message(message.chat.id, "Данные успешно записаны в БД.")
    except Exception as e:
        await bot.send_message(message.chat.id, f"Произошла ошибка при записи данных в БД.\nError: {e}")
        await state.finish()

    await bot.send_message(message.chat.id,
                           f"Создана новая командировка.\n{name}\nДата начала: {start_date_string}\nСтрана: {message.text}",
                           reply_markup=main_keyboard)
    await state.finish()


# ======================================================================================================================
# МОИ КОМАНДИРОВКИ

@dp.message_handler(content_types=types.ContentType.TEXT, state=TripsMenu.waiting_for_trip)
async def text_handler_while_in_menu(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, "Пожалуйста, выберете командировку из меню.")


@dp.callback_query_handler(lambda c: c.data.startswith('id:'), state=TripsMenu.waiting_for_trip)
async def trip_added(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = await state.get_data()
    trips = data.get("trips")
    trips_ids = objects_list_to_ids_list(trips)
    id = str(callback_query.data.split(':')[1])

    if id in trips_ids:
        expenses = session.query(Expense).filter_by(trip_id=int(id)).all()

        if not expenses:
            await bot.send_message(callback_query.message.chat.id,
                                   "У данной командировки нет расходов.\nНажмите кнопку "
                                   "'Добавить расход' в главном меню чтобы добавить.")
            return

        await state.set_state(TripsMenu.waiting_for_expense.state)
        await state.update_data(expenses=expenses)
        await display_expenses(callback_query.message.chat.id, expenses, current_page=0)


@dp.callback_query_handler(lambda c: c.data.startswith('id:'), state=TripsMenu.waiting_for_expense)
async def expense_added(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = await state.get_data()
    expenses = data.get("expenses")
    expenses_ids = objects_list_to_ids_list(expenses)
    id = callback_query.data.split(':')[1]

    if id in expenses_ids:
        expense = session.query(Expense).filter_by(id=int(id)).first()
        delete_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
        delete_keyboard.add(
            InlineKeyboardButton(text="Удалить", callback_data=f"delete_expense:{id}"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_expense_menu")
        )
        await state.set_state(TripsMenu.detail_expense.state)
        await bot.send_message(callback_query.message.chat.id,
                               f"Выбран расход\nСтатья расхода: {expense.category}\nСумма: {expense.amount}\nКоммент: {expense.comment}",
                               reply_markup=delete_keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('delete_expense:'), state=TripsMenu.detail_expense)
async def detail_expense(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    expense_id = callback_query.data.split(':')[1]
    session.query(Expense).filter_by(id=int(expense_id)).delete()
    session.commit()
    await bot.send_message(callback_query.message.chat.id,
                           f"Выбраный расход удален")


# ======================================================================================================================


# Обработчик перелистывания страниц
@dp.callback_query_handler(lambda c: c.data.startswith('paginate_trips:'), state="*")
async def process_trips_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        items = data.get('trips')
        current_trips_page = data.get('current_trips_page', 0)

        direction = callback_query.data.split(':')[1]

        if direction == 'prev_trips_page':
            current_trips_page = max(0, current_trips_page - 1)
        elif direction == 'next_trips_page':
            current_trips_page += 1

        data['current_trips_page'] = current_trips_page

        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=generate_paginator(items, current_trips_page))

    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data.startswith('paginate_expenses:'), state="*")
async def process_expenses_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        items = data.get('expenses')
        current_expenses_page = data.get('current_expenses_page', 0)

        direction = callback_query.data.split(':')[1]

        if direction == 'prev_trips_page':
            current_expenses_page = max(0, current_expenses_page - 1)
        elif direction == 'next_trips_page':
            current_expenses_page += 1

        data['current_expenses_page'] = current_expenses_page

        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=generate_paginator(items, current_expenses_page))

    await bot.answer_callback_query(callback_query.id)


# ======================================================================================================================
# Обработчики регистрации пользователя

@dp.message_handler(content_types=types.ContentType.TEXT, state=UserRegistration.waiting_for_fullname)
async def fullname_registration_handler(message: types.Message, state: FSMContext):
    fio = message.text
    await state.update_data(fio=fio)
    await state.set_state(UserRegistration.waiting_for_position.state)
    await bot.send_message(message.chat.id, f"Регистрация\nФИО: {fio}\nВведите должность:")


@dp.message_handler(content_types=types.ContentType.TEXT, state=UserRegistration.waiting_for_position)
async def fullname_registration_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    fio = data.get("fio")

    try:
        telegram_id = message.from_user.id
        name = message.from_user.first_name
        position = message.text
        new_user = User(telegram_id=telegram_id, name=name, full_name=fio, position=position)
        session.add(new_user)
        session.commit()
    except Exception as e:
        await bot.send_message(message.chat.id,
                               f"Ошибка при добавлении пользователя в БД.\nID: {message.from_user.id}\nError: {e}")

    await state.finish()
    await bot.send_message(message.chat.id,
                           f"Регистрация завершена\nФИО: {fio}\nДолжность: {position}\nВыберете команду из меню",
                           reply_markup=main_keyboard)


# ======================================================================================================================

if __name__ == '__main__':
    dp.middleware.setup(AuthMiddleware())
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling())
