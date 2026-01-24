from decouple import config
from aiogram import F, Router, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove 
from keyboards.phone_reservation import salon_phone_kb, request_contact_kb, phone_confirm_kb


router = Router()
TG_CHAT_ID = config('ADMIN_CHAT_ID')


SALONS = [
    {
        "id": "salon_1",
        "name": "Beauty City 1",
        "address": "г. Москва, ул. Ленина, 10",
        "phone": "+7-999-111-11-11"
    },
    {
        "id": "salon_2",
        "name": "Beauty City 2",
        "address": "г. Москва, ул. Пушкина, 25",
        "phone": "+7-999-222-22-22"
    }
  ]


class PhoneReservationStates(StatesGroup):
    waiting_for_contact = State()
    waiting_for_time = State()
    confirming = State()


def format_phone_request(data: dict):
    user = data.get("user", {})
    phone = data.get("phone", "—")
    time_pref = data.get("time_pref", "—")
    user_link = f"<a href='tg://user?id={user.get('id')}'>Пользователь</a>" if user else "Пользователь"

    return (
        f"Новая заявка на обратный звонок:\n\n"
        f"{user_link}\n"
        f"Телефон: {phone}\n"
        f"Удобное время для звонка: {time_pref}\n"
    )


def validate_phone(text: str):
    if not text:
        return None
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch == "+")
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if len(digits) < 7:
        return None
    return cleaned


@router.message(F.text == "Запись по телефону")
async def show_phone_buttons(message: types.Message):
    await message.answer(
        "Выберите салон, в котором хотите оформить звонок:",
        reply_markup=None
    )
    kb = salon_phone_kb(SALONS)
    await message.answer("Выберите салон:", reply_markup=kb)


@router.callback_query(F.data.startswith("phone:start:"))
async def phone_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":", 2)
    salon_id = parts[2] if len(parts) > 2 else None
    salon = next((s for s in SALONS if s["id"] == salon_id), None)

    if not salon:
        await callback.message.edit_text("Выбранный салон не найден. Попробуйте снова")
        return

    await state.update_data(user={"id": callback.from_user.id, "name": callback.from_user.full_name})
    await state.update_data(salon=salon)
    await callback.message.answer(
        f"Вы выбрали салон: {salon.get('name')} ({salon.get('address')}).\n"
        "Пожалуйста, отправьте ваш номер телефона удобным для вас способом "
        "(нажав кнопку ниже или введя номер вручную).",
        reply_markup=request_contact_kb()
    )
    await state.set_state(PhoneReservationStates.waiting_for_contact)


@router.message(PhoneReservationStates.waiting_for_contact, F.content_type.in_({"contact", "text"}))
async def phone_receive_contact(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "отмена":
        await message.answer("Запись по телефону отменена", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    phone = None
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = validate_phone(message.text)
        if not phone:
            await message.answer("Неправильный формат номера. Введите номер снова или нажмите 'Отмена'")
            return

    await state.update_data(phone=phone)
    await message.answer(
        "Укажите удобное время для звонка (например: завтра утром, сегодня с 18:00 до 20:00)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(PhoneReservationStates.waiting_for_time)


@router.message(PhoneReservationStates.waiting_for_time, F.content_type == "text")
async def phone_receive_time(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == "отмена":
        await message.answer("Запись по телефону отменена", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    if ";" in text:
        time_pref, note = (part.strip() for part in text.split(";", 1))
    else:
        time_pref = text
        note = ""

    await state.update_data(time_pref=time_pref, note=note)
    data = await state.get_data()

    summary = format_phone_request(data)
    await state.update_data(summary=summary)

    await message.answer(
        "Проверьте, пожалуйста, данные заявки:\n\n" + summary,
        reply_markup=phone_confirm_kb(),
        parse_mode="HTML"
    )
    await state.set_state(PhoneReservationStates.confirming)


@router.callback_query(F.data == "phone:send")
async def phone_send(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    summary = data.get("summary") or format_phone_request(data)

    await callback.message.bot.send_message(chat_id=TG_CHAT_ID, text=summary, parse_mode="HTML")
    await callback.message.edit_text("Ваша заявка отправлена. Наш менеджер свяжется с вами в ближайшее время")
    await state.clear()


@router.callback_query(F.data == "phone:cancel")
async def phone_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Запись отменена")
    await callback.message.edit_text("Запись по телефону отменена пользователем.")
    await state.clear()