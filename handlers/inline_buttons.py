from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards import get_procedure_buttons
from keyboards import get_date_buttons
from keyboards import get_time_buttons
from keyboards import get_salon_buttons


router = Router()

@router.callback_query(F.data == 'procedure_button')
async def start_with_procedure(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Выберите процедуру:',
        reply_markup=get_procedure_buttons()
    )


@router.callback_query(F.data == 'choose_procedure_button')
async def cmd_procedure(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Выберете дату:',
        reply_markup=get_date_buttons(),
    )


@router.callback_query(F.data == 'choose_date_button')
async def cmd_data(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Выберите время:',
        reply_markup=get_time_buttons(),
    )


@router.callback_query(F.data == 'choose_time_button')
async def cmd_time(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Выберите салон',
        reply_markup=get_salon_buttons(),
    )


@router.callback_query(F.data == 'choose_salon_button')
async def cmd_salon(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Спасибо, что выбрали наши услуги!\n'
        'Вы записаны на такую-то процедуру, в такую-то дату и время\n'
        'В такой-то салон, к такому-то мастеру',
    )

# Обработчик команды /hello
# @router.message(Command('hello'))
# async def cmd_hello(message: types.Message):
#     """
#     Показывает сообщение с inline-кнопкой
#     """
#     await message.answer(
#         text="Нажмите на кнопку ниже:",
#         reply_markup=get_hello_keyboard()
#     )

# # Обработчик нажатия на inline-кнопку
# @router.callback_query(F.data == "hello_button")
# async def process_hello_button(callback: types.CallbackQuery):
#     """
#     Обрабатывает нажатие на кнопку
#     """
#     # Отвечаем пользователю
#     await callback.message.answer("Привет! 😊")
    
#     # Подтверждаем нажатие (убираем "часики" на кнопке)
#     await callback.answer()