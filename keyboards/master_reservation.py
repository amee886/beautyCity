from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)


class SpecialistCBData(CallbackData, prefix="spec"):
    spec: str


class ProcedureCBData(CallbackData, prefix="proc"):
    spec: str
    proc: str


class DateCBData(CallbackData, prefix="date"):
    spec: str
    date: str


class TimeCBData(CallbackData, prefix="time"):
    spec: str
    date: str
    salon: str
    time: str


class ConfirmCBData(CallbackData, prefix="confirm"):
    action: str


def generate_master_kb(specialists):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for specialist in specialists:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=specialist["name"], 
                    callback_data=SpecialistCBData(spec=specialist['id']).pack()
                )
            ]
        )

    return keyboard


def generate_procedure_kb(spec_id, procedures):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for proc in procedures:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=proc["name"],
                    callback_data=ProcedureCBData(spec=spec_id, proc=proc["id"]).pack(),
                )
            ]
        )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="master_reservation")])
    return keyboard


def generate_date_kb(spec_id, dates):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for date in dates:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=date,
                    callback_data=DateCBData(spec=spec_id, date=date).pack(),
                )
            ]
        )
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="Назад", callback_data=SpecialistCBData(spec=spec_id).pack())]
    )

    return keyboard


def generate_time_kb(spec_id, date, schedule_for_date, salons_map):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for salon_id, times in schedule_for_date.items():
        salon_name = salons_map.get(salon_id, salon_id)
        for time in times:
            text = f"{time} ({salon_name})"
            safe_time = time.replace(":", "-")
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=text,
                        callback_data=TimeCBData(spec=spec_id, date=date, salon=salon_id, time=safe_time).pack(),
                    )
                ]
            )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data=DateCBData(spec=spec_id, date=date).pack())])

    return keyboard


def generate_personal_data_kb():
    keyboard = InlineKeyboardMarkup(inline_key_board=[
        [
            InlineKeyboardButton(text="Согласен(на) на обработку пд", callback_data=ConfirmCBData(action="accept_personal").pack()),
            InlineKeyboardButton(text="Не согласен(на) на обработку пд", callback_data=ConfirmCBData(action="decline_personal").pack()),
        ]
    ])

    return keyboard


def generate_confirm_reservation_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить запись", callback_data=ConfirmCBData(action="finalize").pack()),
            InlineKeyboardButton(text="Отменить", callback_data=ConfirmCBData(action="cancel").pack()),
        ]
    ])

    return keyboard


def generate_request_contact_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт", request_contact=True)],
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard