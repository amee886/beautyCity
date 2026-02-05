from aiogram import F, Router, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from keyboards.master_reservation import (
    SpecialistCBData,
    ProcedureCBData,
    DateCBData,
    TimeCBData,
    ConfirmCBData,
    generate_master_kb,
    generate_procedure_kb,
    generate_date_kb,
    generate_time_kb,
    generate_personal_data_kb,
    generate_confirm_reservation_kb,
    generate_request_contact_kb,
    get_promocode_kb
)

from config import SALONS, PROCEDURES, SPECIALISTS, PROMOCODES
from db_utils import save_appointment


SALONS_MAP = {s["id"]: s["name"] for s in SALONS}
PROCS_MAP = {p["id"]: p for p in PROCEDURES}
SPECS_MAP = {s["id"]: s for s in SPECIALISTS}
PROMOCODES_MAP = {c["code"]: c for c in PROMOCODES}


router = Router()


class ReservationStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    choosing_salon = State()
    entering_fio = State()
    entering_phone = State()
    entering_promocode = State()
    confirming_personal = State()
    confirming_reservation = State()


@router.callback_query(F.data == "master_reservation")
@router.message(F.text == "Запись к мастеру")
async def procedure_reservation(update: types.Message | types.CallbackQuery):
    kb = generate_master_kb(SPECIALISTS)
    if isinstance(update, types.Message):
        await update.answer(
            "Выберите мастера:",
            reply_markup=kb
        )
    else:
        await update.message.edit_text(
            "Выберите мастера:",
            reply_markup=generate_master_kb(SPECIALISTS)
        )
        await update.answer()


@router.callback_query(SpecialistCBData.filter())
async def choose_specialist(callback: types.CallbackQuery, callback_data: SpecialistCBData, state: FSMContext):
    await callback.answer()
    spec_id = callback_data.spec
    spec = SPECS_MAP.get(spec_id)
    if not spec:
        if callback.message:
            await callback.message.edit_text("Мастер не найден")
        return

    procs = [PROCS_MAP[p_id] for p_id in spec.get("procedures", []) if p_id in PROCS_MAP]
    kb = generate_procedure_kb(spec_id, procs)
    await state.update_data(spec_id=spec_id)
    if callback.message:
        await callback.message.edit_text(f"Мастер: {spec['name']}\nВыберите процедуру:", reply_markup=kb)


@router.callback_query(ProcedureCBData.filter())
async def choose_procedure(callback: types.CallbackQuery, callback_data: ProcedureCBData, state: FSMContext):
    await callback.answer()
    spec_id = callback_data.spec
    proc_id = callback_data.proc
    spec = SPECS_MAP.get(spec_id)
    proc = PROCS_MAP.get(proc_id)
    if not spec or not proc:
        if callback.message:
            await callback.message.answer("Ошибка выбора процедуры.")
        return

    dates = list(spec.get("schedule", {}).keys())
    if not dates:
        if callback.message:
            await callback.message.edit_text("Нет доступных дат у этого мастера.")
        return

    await state.update_data(proc_id=proc_id)
    await state.set_state(ReservationStates.choosing_date)
    kb = generate_date_kb(spec_id, dates)
    if callback.message:
        await callback.message.edit_text(f"Процедура: {proc['name']}\nВыберите дату:", reply_markup=kb)


@router.callback_query(DateCBData.filter())
async def choose_date(callback: types.CallbackQuery, callback_data: DateCBData, state: FSMContext):
    await callback.answer()
    spec_id = callback_data.spec
    date = callback_data.date
    spec = SPECS_MAP.get(spec_id)
    if not spec:
        if callback.message:
            await callback.message.answer("Мастер не найден.")
        return

    schedule = spec.get("schedule", {})
    if date not in schedule:
        if callback.message:
            await callback.message.edit_text("На выбранную дату нет расписания.")
        return

    schedule_for_date = schedule[date]
    kb = generate_time_kb(spec_id, date, schedule_for_date, SALONS_MAP)
    await state.update_data(date=date)
    await state.set_state(ReservationStates.choosing_time)
    if callback.message:
        await callback.message.edit_text(f"Выберите время ({date}):", reply_markup=kb)


@router.callback_query(TimeCBData.filter())
async def choose_time(callback: types.CallbackQuery, callback_data: TimeCBData, state: FSMContext):
    await callback.answer()
    spec_id = callback_data.spec
    date = callback_data.date
    salon_id = callback_data.salon
    time = callback_data.time.replace("-", ":")

    await state.update_data(salon_id=salon_id, time=time)
    await state.set_state(ReservationStates.entering_fio)

    salon = next((s for s in SALONS if s["id"] == salon_id), None)
    salon_text = salon["name"] if salon else salon_id
    text = (
        f"Вы выбрали:\n"
        f"Мастер: {SPECS_MAP[spec_id]['name']}\n"
        f"Дата: {date}\n"
        f"Время: {time}\n"
        f"Салон: {salon_text}\n\n"
        "Введите ФИО клиента:"
    )
    if callback.message:
        await callback.message.edit_text(text)


@router.message(ReservationStates.entering_fio)
async def enter_fio(message: types.Message, state: FSMContext):
    fio = (message.text or "").strip()
    if not fio:
        await message.reply("ФИО не может быть пустым, введите, пожалуйста")
        return
    await state.update_data(fio=fio)
    await state.set_state(ReservationStates.entering_phone)
    kb = generate_request_contact_kb()
    await message.answer("Пожалуйста, отправьте номер телефона (можно нажать кнопку ниже):", reply_markup=kb)


@router.message(ReservationStates.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        text = (message.text or "").strip()
        if text.lower() == "отмена":
            await state.clear()
            await message.answer("Запись отменена", reply_markup=types.ReplyKeyboardRemove())
            return
        phone = text

    if not phone or len(phone) < 5:
        await message.reply("Пожалуйста, введите корректный номер телефона")
        return

    await state.update_data(phone=phone)
    await state.set_state(ReservationStates.entering_promocode)

    await message.answer(
        text="Введите промокод, чтобы получить скидку!",
        reply_markup=get_promocode_kb()
    )


@router.message(ReservationStates.entering_promocode)
async def enter_promocode(message: types.Message, state: FSMContext):
    """Обработка ожидания промокода от пользователя."""
    users_promocode = message.text.strip().lower()

    if users_promocode in PROMOCODES_MAP:
        discount_percent = PROMOCODES_MAP[users_promocode]["discount_percent"]
        await message.answer(
            text=f"Поздравляем! Вы получили скидку {discount_percent}%"
        )
        await state.update_data(discount_percent=discount_percent)
        await state.set_state(ReservationStates.confirming_personal)
        await message.answer(
            text="Необходимо ваше согласие на обработку персональных данных",
            reply_markup=generate_personal_data_kb(),
        )
    else:
        await message.answer(
            text="К сожалению такого промокода не существует :(\nПопробуете ещё раз",
            reply_markup=get_promocode_kb()
        )


@router.callback_query(F.data == "continue")
async def skip_promocode(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ReservationStates.confirming_personal)

    await callback.message.answer(
        text="Необходимо ваше согласие на обработку персональных данных",
        reply_markup=generate_personal_data_kb(),
    )


@router.callback_query(ConfirmCBData.filter())
async def handle_confirm(callback: types.CallbackQuery, callback_data: ConfirmCBData, state: FSMContext):
    await callback.answer()
    action = callback_data.action

    if action == "accept_personal":
        data = await state.get_data()
        spec = SPECS_MAP.get(data.get("spec_id"))
        proc = PROCS_MAP.get(data.get("proc_id"))
        salon = next((s for s in SALONS if s["id"] == data.get("salon_id")), None)
        date = data.get("date")
        time = data.get("time")
        fio = data.get("fio")
        phone = data.get("phone")
        discount = data.get("discount_percent")

        price = proc["prices"].get(salon["id"]) if proc and salon else None

        if discount:
            price = price * (100 - discount) / 100

        pricetext = f"\nСтоимость: {price}р" if price else ""

        summary = (
            f"Подтвердите запись:\n\n"
            f"Мастер: {spec['name']}\n"
            f"Процедура: {proc['name']}{pricetext}\n"
            f"Дата: {date}\n"
            f"Время: {time}\n"
            f"Салон: {salon['name']}\n\n"
            f"Клиент: {fio}\n"
            f"Телефон: {phone}\n"
        )

        await state.set_state(ReservationStates.confirming_reservation)
        if callback.message:
            await callback.message.edit_text(summary, reply_markup=generate_confirm_reservation_kb())
        return

    if action == "decline_personal":
        await state.clear()
        if callback.message:
            await callback.message.edit_text("Для записи требуется согласие на обработку персональных данных. Запись отменена.")
        return

    if action == "finalize":
        data = await state.get_data()
        spec = SPECS_MAP.get(data.get("spec_id"))
        proc = PROCS_MAP.get(data.get("proc_id"))
        salon = next((s for s in SALONS if s["id"] == data.get("salon_id")), None)
        date = data.get("date")
        time = data.get("time")
        fio = data.get("fio")
        phone = data.get("phone")

        await state.clear()
        if callback.message:
            await callback.message.edit_text("Ваша запись подтверждена. Спасибо!")
        return

    if action == "cancel":
        await state.clear()
        if callback.message:
            await callback.message.edit_text("Запись отменена.")
        return