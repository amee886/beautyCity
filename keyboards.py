from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text='В начало')],
        [KeyboardButton(text='📋 Помощь')],
        [KeyboardButton(text='ℹ️ О нас')]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_inline_keyboard() -> InlineKeyboardMarkup:
    procedure_button = InlineKeyboardButton(
        text='Выборать процедуру',
        callback_data='procedure_button',
    )
    master_button = InlineKeyboardButton(
        text='Выбрать мастера',
        callback_data='choose_master_button',
    )
    salon_button = InlineKeyboardButton(
        text='Выбрать салон',
        callback_data='choose_master_button',
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [procedure_button],
            [master_button],
            [salon_button],
        ],
    )
    
    return keyboard


def get_procedure_buttons() -> InlineKeyboardMarkup:
    procedure_button = InlineKeyboardButton(
        text='Маник',
        callback_data='choose_procedure_button',
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [procedure_button],
        ],
    )

    return keyboard


def get_date_buttons() -> InlineKeyboardMarkup:
    date_button = InlineKeyboardButton(
        text='Дата',
        callback_data='choose_date_button',
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [date_button],
        ],
    )

    return keyboard


def get_time_buttons() -> InlineKeyboardMarkup:
    time_button = InlineKeyboardButton(
        text='Время',
        callback_data='choose_time_button',
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [time_button],
        ]
    )

    return keyboard


def get_salon_buttons() -> InlineKeyboardMarkup:
    salon_button = InlineKeyboardButton(
        text='Салон №1',
        callback_data='choose_salon_button',
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [salon_button]
        ]
    )

    return keyboard