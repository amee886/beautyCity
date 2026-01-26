from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)


class CategoryCBData(CallbackData, prefix="category"):
    category: str      


def generate_catalog_kb(procedures):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for proc in procedures:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=proc["name"], 
                    callback_data=CategoryCBData(category=proc['id']).pack()
                )
            ]
        )

    return keyboard


def make_dates_kb(dates):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for d in dates:
        try:
            dt = datetime.fromisoformat(d).date()
            text = dt.strftime("%Y-%m-%d (%a)")
        except Exception:
            text = d
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"proc_date:{d}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="procedure_reservation")])
    return kb


def make_times_kb(times):
    available = set(str(t).strip() for t in (times or []))
    all_times = ["09:00", "09:30", "10:00", "10:30", "11:00", "12:00", "13:00", "14:00", "15:00"]
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if not available and all_times is None:
        kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="procedure_reservation")])
        return kb

    if all_times is None:
        for t in sorted(available):
            kb.inline_keyboard.append([InlineKeyboardButton(text=t, callback_data=f"proc_time:{t}")])
    else:
        for t in all_times:
            tt = str(t).strip()
            if tt in available:
                kb.inline_keyboard.append([InlineKeyboardButton(text=tt, callback_data=f"proc_time:{tt}")])
            else:
                kb.inline_keyboard.append([InlineKeyboardButton(text=f"{tt} (нет мест)", callback_data=f"notime:{tt}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="procedure_reservation")])
    return kb


def make_salons_kb(salons):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s in salons:
        display = s.get("name") + (f" — {s.get('address')}" if s.get("address") else "")
        kb.inline_keyboard.append([InlineKeyboardButton(text=display, callback_data=f"proc_salon:{s['id']}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="procedure_reservation")])
    return kb


def make_consent_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Согласен(на) на обработку ПД", callback_data="pd:accept"),
            InlineKeyboardButton(text="Не согласен(на)", callback_data="pd:decline"),
            ]
        ]
    )
    return kb


def make_request_contact_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт", request_contact=True)],
            [KeyboardButton(text="Ввести вручную")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return kb


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