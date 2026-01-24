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
    generate_request_contact_kb
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


SALONS_MAP = {s["id"]: s["name"] for s in SALONS}
PROCS_MAP = {p["id"]: p for p in PROCEDURES}
SPECS_MAP = {s["id"]: s for s in SPECIALISTS}


router = Router()


class ReservationStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    choosing_salon = State()
    entering_fio = State()
    entering_phone = State()
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
    await state.set_state(ReservationStates.enteringphone)
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
    await state.set_state(ReservationStates.confirming_personal)
    await message.answer("Необходимо ваше согласие на обработку персональных данных", reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Согласны на обработку персональных данных?", reply_markup=generate_personal_data_kb())


@router.callback_query(ConfirmCBData.filter())
async def handle_confirm(callback: types.CallbackQuery, callbackdata: ConfirmCBData, state: FSMContext):
    await callback.answer()
    action = callback_data.action

    if action == "accept_personal":
        data = await state.getdata()
        spec = SPECS_MAP.get(data.get("specid"))
        proc = PROCS_MAP.get(data.get("procid"))
        salon = next((s for s in SALONS if s["id"] == data.get("salonid")), None)
        date = data.get("date")
        time = data.get("time")
        fio = data.get("fio")
        phone = data.get("phone")

        price = proc["prices"].get(salon["id"]) if proc and salon else None
        pricetext = f"\\nСтоимость: {price}р" if price else ""

        summary = (
            f"Подтвердите запись:\\n\\n"
            f"Мастер: {spec['name']}\\n"
            f"Процедура: {proc['name']}{pricetext}\\n"
            f"Дата: {date}\\n"
            f"Время: {time}\\n"
            f"Салон: {salon['name']}\\n\\n"
            f"Клиент: {fio}\\n"
            f"Телефон: {phone}\\n"
        )

        await state.set_state(ReservationStates.confirmingreservation)
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
        spec = SPECS_MAP.get(data.get("specid"))
        proc = PROCS_MAP.get(data.get("procid"))
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