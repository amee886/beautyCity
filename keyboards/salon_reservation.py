from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)


class SalonCBData(CallbackData, prefix="salon"):
    salon: str


class ProcedureCBData(CallbackData, prefix="proc"):
    proc: str


class DateCBData(CallbackData, prefix="date"):
    date: str


class TimeCBData(CallbackData, prefix="time"):
    spec: str
    time: str


class ConfirmCBData(CallbackData, prefix="confirm"):
    action: str


def generate_salon_kb(salons):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for salon in salons:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{salon['name']} ({salon['address']})",
                    callback_data=SalonCBData(salon=salon['id']).pack()
                )
            ]
        )

    return keyboard


def generate_procedure_kb(salon_id, procedures):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for proc in procedures:
        price = proc.get("prices", {}).get(salon_id, "—")
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{proc.get('name')} — {price}₽",
                    callback_data=ProcedureCBData(proc=proc['id']).pack()
                )
            ]
        )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="salon_reservation")])
    return keyboard


def generate_date_kb(salon_id, procedures, specialists):
    dates = set()
    for spec in specialists:
        schedule = spec.get("schedule", {})
        for date, salons_map in schedule.items():
            if salon_id in salons_map and salons_map[salon_id]:
                dates.add(date)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for date in sorted(dates):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=date, callback_data=DateCBData(date=date).pack())
        ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="salon_reservation")])
    return keyboard


def generate_time_kb(salon_id, proc_id, date, specialists):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for spec in specialists:
        if not proc_id or proc_id not in spec.get("procedures", []):
            continue
        schedule = spec.get("schedule", {}).get(date, {})
        times = schedule.get(salon_id, [])
        for time in times:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{time} — {spec.get('name')}",
                    callback_data=TimeCBData(spec=spec['id'], time=time.replace(":", "-")).pack()
                )
            ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="salon_reservation")])
    return keyboard


def generate_personal_data_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Согласен(на) на обработку пд", callback_data=ConfirmCBData(action="accept_personal").pack()),
            InlineKeyboardButton(text="Не согласен(на) на обработку пд", callback_data=ConfirmCBData(action="decline_personal").pack()),
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


def generate_confirm_reservation_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить запись", callback_data=ConfirmCBData(action="finalize").pack()),
            InlineKeyboardButton(text="Отменить", callback_data=ConfirmCBData(action="cancel").pack()),
        ]
    ])

    return keyboard


def get_promocode_kb():
    decline_btn = InlineKeyboardButton(
        text="Пропустить",
        callback_data="continue",
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [decline_btn],
        ]
    )

    return keyboard