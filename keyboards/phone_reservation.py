from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)


def salon_phone_kb(salons: list):
    buttons = []
    for s in salons:
        buttons.append(
            [
                InlineKeyboardButton(
                text=f"Записаться по телефону — {s.get('name')}", 
                callback_data=f"phone:start:{s.get('id')}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="Отмена", 
                callback_data="phone:cancel"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def request_contact_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить номер", request_contact=True)],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return kb


def phone_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить запрос менеджеру", callback_data="phone:send")],
        [InlineKeyboardButton(text="Отменить", callback_data="phone:cancel")],
    ])
