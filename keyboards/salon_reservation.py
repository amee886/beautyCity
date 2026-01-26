from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)


class SalonCB(CallbackData, prefix="salon"):
    salon: str

class ProcedureCB(CallbackData, prefix="proc"):
    proc: str

class DateCB(CallbackData, prefix="date"):
    date: str

class TimeCB(CallbackData, prefix="time"):
    spec: str
    time: str

class ConfirmCB(CallbackData, prefix="confirm"):
    ok: str


def generate_salons_kb(salons):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for salon in salons:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{salon['name']} ({salon['address']})",
                    callback_data=SalonCB(salon=salon['id']).pack()
                )
            ]
        )

    return keyboard


def generate_procedures_kb(procedures, salon_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for procedure in procedures:
        price = procedure.get("prices", {}).get(salon_id, "—")
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{procedure.get('name')} — {price}₽",
                    callback_data=ProcedureCB(proc=procedure['id']).pack()
                )
            ]
        )

    return keyboard


def generate_dates_kb(salon_id, proc_id, specialists):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    dates = set()
    for spec in specialists:
        if proc_id not in spec.get("procedures", []):
            continue
        for date, salons in spec.get("schedule", {}).items():
            if salon_id in salons and salons[salon_id]:
                dates.add(date)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for date in sorted(dates):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=date, callback_data=DateCB(date=date).pack())
        ])
    return keyboard


def generate_time_kb(salon_id, proc_id, date, specialists):
    buttons = []
    for spec in specialists:
        if proc_id not in spec.get("procedures", []):
            continue
        times = spec.get("schedule", {}).get(date, {}).get(salon_id, [])
        for time in times:
            time = time.replace(":", "-")
            buttons.append([
                InlineKeyboardButton(
                    text=f"{time} — {spec.get('name')}",
                    callback_data=TimeCB(spec=spec['id'], time=time).pack()
                )
            ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def generate_confirm_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Согласен(на) на обработку ПД", callback_data="pd:accept"),
            InlineKeyboardButton(text="Не согласен(на)", callback_data="pd:decline"),
            ]
        ]
    )
    return kb


def generate_request_contact_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт", request_contact=True)],
            [KeyboardButton(text="Ввести вручную")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def make_confirmation_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить запись", callback_data="res:confirm")],
        [InlineKeyboardButton(text="Отменить", callback_data="res:cancel")],
    ])


def get_promocode_kb():
    """Создать клавиатуру для шага с промокодом."""
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