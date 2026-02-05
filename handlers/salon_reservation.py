from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from keyboards.salon_reservation import (
    SalonCBData,
    ProcedureCBData,
    DateCBData,
    TimeCBData,
    ConfirmCBData,
    generate_salon_kb, 
    generate_procedure_kb,
    generate_date_kb,
    generate_time_kb,
    generate_personal_data_kb,
    generate_request_contact_kb,
    generate_confirm_reservation_kb,
    get_promocode_kb
)
from config import SALONS, PROCEDURES, SPECIALISTS, PROMOCODES


SALONS_MAP = {s["id"]: s for s in SALONS}
PROCS_MAP = {p["id"]: p for p in PROCEDURES}
SPECS_MAP = {s["id"]: s for s in SPECIALISTS}
PROMOCODES_MAP = {c["code"]: c for c in PROMOCODES}


router = Router()


class ReservationStates(StatesGroup):
    choosing_salon = State()
    choosing_procedure = State()
    choosing_date = State()
    choosing_time = State()
    entering_fio = State()
    entering_phone = State()
    entering_promocode = State()
    confirming_personal = State()
    confirming_reservation = State()


@router.callback_query(F.data == "salon_reservation")
@router.message(F.text == "Запись по салону")
async def salon_reservation(update: types.Message | types.CallbackQuery, state: FSMContext):
    kb = generate_salon_kb(SALONS)
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
    await state.set_state(ReservationStates.choosing_salon)


@router.callback_query(SalonCBData.filter())
async def choose_salon(callback: types.CallbackQuery, callback_data: SalonCBData, state: FSMContext):
    salon_id = callback_data.salon
    salon = SALONS_MAP.get(salon_id, {})
    await state.update_data(salon_id=salon_id, salon_name=salon.get("name"))
    kb = generate_procedure_kb(salon_id, PROCEDURES)
    await callback.message.edit_text(f"Выбран салон: {salon.get('name')}\nВыберите процедуру:", reply_markup=kb)
    await state.set_state(ReservationStates.choosing_procedure)
    await callback.answer()


@router.callback_query(ProcedureCBData.filter())
async def choose_procedure(callback: types.CallbackQuery, callback_data: ProcedureCBData, state: FSMContext):
    proc_id = callback_data.proc
    proc = PROCS_MAP.get(proc_id, {})
    await state.update_data(proc_id=proc_id, proc_name=proc.get("name"), proc_price=proc.get("prices", {}))
    data = await state.get_data()
    salon_id = data.get("salon_id")
    kb = generate_date_kb(salon_id, PROCEDURES, SPECIALISTS)
    await callback.message.edit_text(f"Процедура: {proc.get('name')}\nВыберите дату:", reply_markup=kb)
    await state.set_state(ReservationStates.choosing_date)
    await callback.answer()


@router.callback_query(DateCBData.filter())
async def choose_date(callback: types.CallbackQuery, callback_data: DateCBData, state: FSMContext):
    date = callback_data.date
    await state.update_data(date=date)
    data = await state.get_data()
    salon_id = data.get("salon_id")
    proc_id = data.get("proc_id")
    kb = generate_time_kb(salon_id, proc_id, date, SPECIALISTS)
    if not kb.inline_keyboard:
        await callback.answer("Свободных времён на эту дату нет", show_alert=True)
        return
    await callback.message.edit_text("Выберите время (вместе с мастером):", reply_markup=kb)
    await state.set_state(ReservationStates.choosing_time)
    await callback.answer()


@router.callback_query(TimeCBData.filter())
async def choose_time(callback: types.CallbackQuery, callback_data: TimeCBData, state: FSMContext):
    spec_id = callback_data.spec
    time = callback_data.time.replace("-", ":")
    spec = SPECS_MAP.get(spec_id, {})
    if not spec:
        await callback.answer("Мастер не найден", show_alert=True)
        return

    await state.update_data(spec_id=spec_id, spec_name=spec.get("name"), time=time)
    await state.set_state(ReservationStates.entering_fio)

    data = await state.get_data()
    salon_id = data.get("salon_id")
    proc_id = data.get("proc_id")
    date = data.get("date")
    salon = next((s for s in SALONS if s["id"] == salon_id), None)
    proc = PROCS_MAP.get(proc_id)
    salon_text = salon["name"] if salon else salon_id
    proc_text = proc["name"] if proc else proc_id
    text = (
        f"Вы выбрали:\n"
        f"Мастер: {spec.get('name')}\n"
        f"Процедура: {proc_text}\n"
        f"Дата: {date}\n"
        f"Время: {time}\n"
        f"Салон: {salon_text}\n\n"
        "Введите ФИО клиента:"
    )
    if callback.message:
        await callback.message.edit_text(text)
    await callback.answer()


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


@router.message(ReservationStates.entering_phone, F.contact)
async def phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number.strip()
    await state.update_data(phone=phone)
    await message.answer("Контакт получен", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReservationStates.entering_promocode)
    await message.answer(
        text="Введите промокод, чтобы получить скидку!",
        reply_markup=get_promocode_kb()
    )


@router.message(ReservationStates.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
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
        print("DEBUG handle_confirm data:", data)

        spec_id = data.get("spec_id")
        proc_id = data.get("proc_id")
        salon_id = data.get("salon_id")
    
        spec_name = SPECS_MAP.get(spec_id, {}).get("name", "—") if spec_id else "—"
        proc_name = PROCS_MAP.get(proc_id, {}).get("name", "—") if proc_id else "—"
        salon_name = SALONS_MAP.get(salon_id, {}).get("name", "-") if salon_id else "-"

        date = data.get("date", "-")
        time = data.get("time", "-")
        fio = data.get("fio", "-")
        phone = data.get("phone", "-")
        discount = data.get("discount_percent")

        proc_price = PROCS_MAP.get(proc_id, {}).get("prices", {}) if proc_id else {}
        price = proc_price.get(salon_id) if salon_id and proc_price else None
        if discount and price:
            price = price * (100 - discount) / 100
        pricetext = f"\nСтоимость: {price}р" if price else ""

        summary = (
            f"Подтвердите запись:\n\n"
            f"Мастер: {spec_name}\n"
            f"Процедура: {proc_name}{pricetext}\n"
            f"Дата: {date}\n"
            f"Время: {time}\n"
            f"Салон: {salon_name}\n\n"
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