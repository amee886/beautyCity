from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from keyboards.salon_reservation import (
    SalonCB,
    ProcedureCB,
    DateCB,
    TimeCB,
    ConfirmCB,
    generate_salons_kb, 
    generate_procedures_kb,
    generate_dates_kb,
    generate_time_kb,
    generate_confirm_kb,
    generate_request_contact_kb,
    make_confirmation_kb
)


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


SPECIALISTS = [
    {
        "id": "spec_1",
        "name": "Анна",
        "procedures": ["proc_1", "proc_2"],
        "schedule": {
            "2026-01-25": {
                "salon_1": ["10:00", "12:00", "15:00"],
                "salon_2": ["11:00", "14:00"]
            },
        }
    },
    {
        "id": "spec_2",
        "name": "Игорь",
        "procedures": ["proc_1"],
        "schedule": {
            "2026-01-25": {
                "salon_1": ["11:00", "13:00"]
            }
        }
    }
]


PROCEDURES = [
    {
        "id": "proc_1",
        "name": "Стрижка",
        "duration_min": 60,
        "prices": {
            "salon_1": 1500,
            "salon_2": 1400
        }
    },
    {
        "id": "proc_2",
        "name": "Маникюр",
        "duration_min": 90,
        "prices": {
            "salon_1": 2000,
            "salon_2": 1900
        }
    }
]


router = Router()


class SalonReservationStates(StatesGroup):
    choosing_salon = State()
    choosing_procedure = State()
    choosing_date = State()
    choosing_time = State()
    entering_fio = State()
    entering_phone = State()
    confirming = State()


def get_salon_by_id(salon_id):
    for s in SALONS:
        if s["id"] == salon_id:
            return s
    return None


def get_proc_by_id(proc_id):
    for p in PROCEDURES:
        if p.get("id") == proc_id:
            return p
    return None


def get_spec_by_id(spec_id):
    for sp in SPECIALISTS:
        if sp.get("id") == spec_id:
            return sp
    return None


@router.callback_query(F.data == "reserve_by_salon")
@router.message(F.text == "Запись по салону")
async def reserve_by_salon(update: types.Message | types.CallbackQuery):
    kb = generate_salons_kb(SALONS)
    if isinstance(update, types.Message):
        await update.answer(
            "Выберите салон:",
            reply_markup=kb
        )
    else:
        await update.message.edit_text(
            "Выберите салон:",
            reply_markup=kb
        )
        await update.answer()


@router.callback_query(SalonCB.filter(), F.data.startswith("salon:" ))
async def salon_chosen(callback: types.CallbackQuery, callback_data: SalonCB, state: FSMContext):
    salon_id = callback_data.salon
    salon = get_salon_by_id(salon_id)
    if not salon:
        await callback.answer("Салон не найден", show_alert=True)
        return
    await state.update_data(salon_id=salon_id)
    await callback.message.edit_text(
        f"Вы выбрали {salon['name']}\nВыберите процедуру:",
        reply_markup=generate_procedures_kb(PROCEDURES, salon_id)
    )
    await state.set_state(SalonReservationStates.choosing_procedure)
    await callback.answer()


@router.callback_query(ProcedureCB.filter(), F.data.startswith("proc:"))
async def procedurechosen(callback: types.CallbackQuery, callback_data: ProcedureCB, state: FSMContext):
    proc_id = callback_data.proc
    proc = get_proc_by_id(proc_id)
    if not proc:
        await callback.answer("Процедура не найдена", show_alert=True)
        return
    st = await state.get_data()
    salon_id = st.get("salon_id")
    await state.update_data(proc_id=proc_id)
    await callback.message.edit_text(
        f"Процедура: {proc['name']}\nВыберите дату:",
        reply_markup=generate_dates_kb(salon_id, proc_id, SPECIALISTS)
    )
    await state.set_state(SalonReservationStates.choosing_date)
    await callback.answer()


@router.callback_query(DateCB.filter(), F.data.startswith("date:"))
async def choose_date(callback: types.CallbackQuery, callback_data: DateCB, state: FSMContext):
    date = callback_data.date
    st = await state.get_data()
    salon_id = st.get("salon_id")
    proc_id = st.get("proc_id")
    await state.update_data(date=date)
    kb = generate_time_kb(salon_id, proc_id, date, SPECIALISTS)
    if not kb.inline_keyboard:
        await callback.answer("Свободных времён на эту дату нет", show_alert=True)
        return
    await callback.message.edit_text("Выберите время (вместе с мастером):", reply_markup=kb)
    await state.set_state(SalonReservationStates.choosing_time)
    await callback.answer()


@router.callback_query(TimeCB.filter(), F.data.startswith("time:"))
async def choose_time(callback: types.CallbackQuery, callback_data: TimeCB, state: FSMContext):
    spec_id = callback_data.spec
    time = callback_data.time
    spec = get_spec_by_id(spec_id)
    if not spec:
        await callback.answer("Мастер не найден", show_alert=True)
        return
    await state.update_data(spec_id=spec_id, time=time)
    await state.set_state(SalonReservationStates.entering_fio)
    await callback.message.edit_text("Введите, пожалуйста, ваше ФИО:")
    await callback.answer()


@router.message(SalonReservationStates.entering_fio)
async def enter_fio(message: types.Message, state: FSMContext):
    fio = (message.text or "").strip()
    if not fio:
        await message.reply("Пожалуйста, введите корректное ФИО.")
        return

    await state.update_data(fio=fio)
    await state.set_state(SalonReservationStates.entering_phone)
    await message.answer(
        "Хорошо! Отправьте номер телефона (или нажмите «Отправить контакт»):",
        reply_markup=generate_request_contact_kb()
    )


@router.message(SalonReservationStates.entering_phone, F.contact)
async def phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number.strip()
    await state.update_data(phone=phone)
    await message.answer("Контакт получен", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SalonReservationStates.confirming)
    await message.answer("Необходимо ваше согласие на обработку персональных данных", reply_markup=generate_confirm_kb())


@router.message(SalonReservationStates.entering_phone)
async def phone_text(message: types.Message, state: FSMContext):
    phone = (message.text or "").strip()

    if phone == "Ввести вручную":
        await message.reply("Пожалуйста, введите номер телефона вручную (например, +7**********).")
        return

    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        await message.reply("Пожалуйста, введите корректный номер телефона.")
        return

    await state.update_data(phone=phone)
    await state.set_state(SalonReservationStates.confirming)
    await message.answer("Спасибо, номер получен.", reply_markup=ReplyKeyboardRemove())
    await message.answer("Необходимо ваше согласие на обработку персональных данных.", reply_markup=generate_confirm_kb())


@router.callback_query(F.data == ConfirmCB(ok="yes").pack())
async def pd_consent_yes(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Спасибо за согласие")
    await state.update_data(personal_data_consent=True)
    await state.set_state(SalonReservationStates.confirming)

    data = await state.get_data()
    proc = data.get("procedure")
    proc_name = proc.get("name") if isinstance(proc, dict) else (proc or "—")
    proc_price = proc.get("price") if isinstance(proc, dict) else None

    salon = data.get("salon")
    salon_name = salon.get("name", "-")

    master = data.get("master") or {}
    master_name = master.get("name", "—")

    fio = data.get("fio", "-")
    phone = data.get("phone", "-")
    date = data.get("date", "-")
    time = data.get("time", "-")
    price_text = f" — {proc_price}₽" if proc_price is not None else ""
    summary = (
        f"Пожалуйста, подтвердите запись:\n\n"
        f"Салон: {salon_name}\n"
        f"Процедура: {proc_name}{price_text}\n"
        f"Дата: {date}\n"
        f"Время: {time}\n"
        f"Мастер: {master_name}\n"
        f"ФИО: {fio}\n"
        f"Телефон: {phone}\n\n"
    )

    await state.update_data(summary=summary)
    await callback.message.edit_text(
        summary, 
        reply_markup=generate_confirm_kb()
    )

@router.callback_query(F.data == ConfirmCB(ok="no").pack())
async def pd_consent_no(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Вы не дали согласие")
    await callback.message.edit_text("Для оформления записи необходимо согласие на обработку персональных данных. Запись отменена.")
    await state.clear()


@router.callback_query(F.data == "res:confirm")
async def handle_res_confirm(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Запись подтверждена")
    data = await state.getdata()
    summary = data.get("summary", "Ваша запись сохранена.")
    await callback.message.edit_text(f"Ваша запись подтверждена\n\n{summary}")
    await state.clear()


@router.callback_query(F.data == "res:cancel")
async def handle_res_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Запись отменена")
    await callback.message.edit_text("Запись отменена пользователем")
    await state.clear()