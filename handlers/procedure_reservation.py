import asyncio
from decouple import config
from aiogram import F, Router, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime, timedelta
from keyboards.procedure_reservation import (
    generate_catalog_kb, 
    CategoryCBData,
    make_dates_kb,
    make_times_kb,
    make_salons_kb,
    make_consent_kb,
    make_request_contact_kb,
    make_confirmation_kb,
    get_promocode_kb,
    generate_payment_kb
)
from config import SALONS, PROCEDURES, SPECIALISTS, PROMOCODES
from db_utils import save_appointment


PROMOCODES_MAP = {c["code"]: c for c in PROMOCODES}


router = Router()


class ProcReservationStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    choosing_salon = State()
    entering_fio = State()
    entering_phone = State()
    entering_promocode = State()
    confirming_personal = State()
    confirming_reservation = State()
    choosing_payment = State()


def create_paymaster_invoice(amount, description, order_id):
    return f"https://example.com/pay/{order_id}"


@router.callback_query(F.data == "procedure_reservation")
@router.message(F.text == "Запись по процедуре")
async def procedure_reservation(update: types.Message | types.CallbackQuery):
    kb = generate_catalog_kb(PROCEDURES)
    if isinstance(update, types.Message):
        await update.answer(
            "Выберите процедуру:",
            reply_markup=kb
        )
    else:
        await update.message.edit_text(
            "Выберите процедуру:",
            reply_markup=generate_catalog_kb(PROCEDURES)
        )
        await update.answer()


@router.callback_query(CategoryCBData.filter())
async def category_info(callback: types.CallbackQuery, callback_data: CategoryCBData, state: FSMContext):
    proc_id = callback_data.category
    proc = next((p for p in PROCEDURES if p["id"] == proc_id), None)
    if not proc:
        await callback.answer("Процедура не найдена", show_alert=True)
        return

    dates = [(datetime.now().date() + timedelta(days=i)).isoformat() for i in range(0, 7)]
    await state.update_data(procedure=proc)
    await state.set_state(ProcReservationStates.choosing_date)

    await callback.message.edit_text(
        f"Вы выбрали процедуру: {proc['name']}\nДлительность: {proc.get('duration_min')} мин\n\nВыберите дату:",
        reply_markup=make_dates_kb(dates)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("notime:"))
async def notime_selected(callback: types.CallbackQuery):
    await callback.answer("Нет доступных салонов/мастеров на этот слот. Выберите другое время.", show_alert=True)


@router.callback_query(F.data.startswith("proc_date:"))
async def date_selected(callback: types.CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":", 1)[1]
    await state.update_data(date=date_str)
    await state.set_state(ProcReservationStates.choosing_time)

    data = await state.get_data()
    proc = data.get("procedure")
    proc_id = proc["id"]

    times_set = set()
    for spec in SPECIALISTS:
        if proc_id not in spec.get("procedures", []):
            continue
        sched = spec.get("schedule", {}).get(date_str, {})
        for salon_times in sched.values():
            times_set.update(salon_times)

    times_list = sorted(times_set)
    await callback.message.edit_text(f"Дата: {date_str}\n\nВыберите время:", reply_markup=make_times_kb(times_list))
    await callback.answer()


@router.callback_query(F.data.startswith("proc_time:"))
async def time_selected(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data.split(":", 1)[1]
    await state.update_data(time=time_str)
    await state.set_state(ProcReservationStates.choosing_salon)

    data = await state.get_data()
    proc = data.get("procedure")
    raw_date = data.get("date")
    proc_id = proc.get("id") if isinstance(proc, dict) else str(proc)

    if hasattr(raw_date, "strftime"):
        raw_date = raw_date.strftime("%Y-%m-%d")

    available_salons = {}
    for spec in SPECIALISTS:
        if proc_id not in spec.get("procedures", []):
            continue
        spec_sched = spec.get("schedule", {}).get(raw_date, {})
        for salon_id, times in spec_sched.items():
            if time_str in times:
                available_salons[salon_id] = True

    if not available_salons:
        await callback.message.edit_text(
            "Нет доступных салонов/мастеров на этот слот. Выберите другое время.", reply_markup=make_times_kb([])
        )
        await callback.answer()
        return

    salons_list = [s for s in SALONS if s["id"] in available_salons]

    kb = make_salons_kb(salons_list)
    await callback.message.edit_text(
        f"Время: {time_str}\n\nВыберите салон (в котором есть мастер на этот слот):",
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("proc_salon:"))
async def salon_selected(callback: types.CallbackQuery, state: FSMContext):
    salon_id = callback.data.split(":", 1)[1]
    salon = next((s for s in SALONS if s["id"] == salon_id), None)
    if not salon:
        await callback.answer("Салон не найден", show_alert=True)
        return

    await state.update_data(salon=salon_id)

    data = await state.get_data()
    proc = data.get("procedure")
    date_str = data.get("date")
    time_str = data.get("time")
    proc_id = proc.get("id") if isinstance(proc, dict) else str(proc)

    chosen_master = None
    for spec in SPECIALISTS:
        if proc_id not in spec.get("procedures", []):
            continue
        sched = spec.get("schedule", {}).get(date_str, {})
        times = sched.get(salon_id, [])
        if time_str in times:
            chosen_master = {"id": spec["id"], "name": spec["name"]}
            break

    if not chosen_master:
        await callback.message.edit_text("К сожалению, на выбранный слот мастер не найден. Пожалуйста, начните заново.",
                                         reply_markup=None)
        await state.clear()
        return

    await state.update_data(master=chosen_master)
    await state.set_state(ProcReservationStates.entering_fio)

    await callback.message.edit_text(
        f"Выбран салон: {salon.get('name')}\n"
        f"Мастер: {chosen_master['name']}\n\n"
        "Введите, пожалуйста, ФИО:",
        reply_markup=None
    )


@router.message(ProcReservationStates.entering_fio)
async def enter_fio(message: types.Message, state: FSMContext):
    fio = (message.text or "").strip()
    if not fio:
        await message.reply("Пожалуйста, введите корректное ФИО.")
        return

    await state.update_data(fio=fio)
    await state.set_state(ProcReservationStates.entering_phone)

    await message.answer(
        "Хорошо! Отправьте номер телефона (или нажмите «Отправить контакт»):",
        reply_markup=make_request_contact_kb()
    )


@router.message(ProcReservationStates.entering_phone, F.contact)
async def phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number.strip()
    await state.update_data(phone=phone)
    await message.answer("Контакт получен", reply_markup=ReplyKeyboardRemove())
    # Изменено: переход к entering_promocode вместо confirming_personal
    await state.set_state(ProcReservationStates.entering_promocode)
    await message.answer(
        text="Введите промокод, чтобы получить скидку!",
        reply_markup=get_promocode_kb()
    )


@router.message(ProcReservationStates.entering_phone)
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
    await state.set_state(ProcReservationStates.entering_promocode)
    await message.answer("Спасибо, номер получен.", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        text="Введите промокод, чтобы получить скидку!",
        reply_markup=get_promocode_kb()
    )


@router.message(ProcReservationStates.entering_promocode)
async def enter_promocode(message: types.Message, state: FSMContext):
    """Обработка ожидания промокода от пользователя."""
    users_promocode = message.text.strip().lower()

    if users_promocode in PROMOCODES_MAP:
        discount_percent = PROMOCODES_MAP[users_promocode]["discount_percent"]
        await message.answer(
            text=f"Поздравляем! Вы получили скидку {discount_percent}%"
        )
        await state.update_data(discount_percent=discount_percent)
        await state.set_state(ProcReservationStates.confirming_personal)
        await message.answer(
            text="Необходимо ваше согласие на обработку персональных данных",
            reply_markup=make_consent_kb(),
        )
    else:
        await message.answer(
            text="К сожалению такого промокода не существует :(\nПопробуете ещё раз",
            reply_markup=get_promocode_kb()
        )


@router.callback_query(F.data == "continue")
async def skip_promocode(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ProcReservationStates.confirming_personal)

    await callback.message.answer(
        text="Необходимо ваше согласие на обработку персональных данных",
        reply_markup=make_consent_kb(),
    )


@router.callback_query(F.data.startswith("pd:"))
async def handle_pd(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    if action == "decline":
        await callback.answer()
        await callback.message.edit_text("Для оформления записи необходимо согласие на обработку персональных данных. Запись отменена")
        await state.clear()
        return

    await callback.answer()
    await state.update_data(personal_data_consent=True)
    await state.set_state(ProcReservationStates.choosing_payment)

    data = await state.get_data()
    proc = data.get("procedure")
    proc_name = proc.get("name") if isinstance(proc, dict) else (proc or "—")
    salon = next((s for s in SALONS if s["id"] == data.get("salon")), {})
    salon_name = salon.get("name", "-")
    master = data.get("master") or {}
    master_name = master.get("name", "—")
    fio = data.get("fio", "-")
    phone = data.get("phone", "-")
    date = data.get("date", "-")
    time = data.get("time", "-")
    discount = data.get("discount_percent")

    price = proc["prices"].get(salon["id"]) if proc and salon else None
    if discount and price:
        price = price * (100 - discount) / 100

    summary = (
        f"Пожалуйста, подтвердите запись:\n\n"
        f"Процедура: {proc_name}\n"
        f"Дата: {date}\n"
        f"Время: {time}\n"
        f"Салон: {salon_name}\n"
        f"Мастер: {master_name}\n"
        f"ФИО: {fio}\n"
        f"Телефон: {phone}\n\n"
    )

    await state.update_data(summary=summary, price=price)
    payment_kb = generate_payment_kb(price)
    await callback.message.edit_text(
        summary + "Выберите способ оплаты:",
        reply_markup=payment_kb
    )


@router.callback_query(F.data.startswith("pay:"))
async def handle_payment(callback: types.CallbackQuery, state: FSMContext):
    payment_method = callback.data.split(":", 1)[1]
    await state.update_data(payment_method=payment_method)

    data = await state.get_data()
    price = data.get("price")
    summary = data.get("summary")

    if payment_method == "online" and price:
        order_id = f"order_{callback.from_user.id}_{datetime.now().timestamp()}"
        payment_url = create_paymaster_invoice(price, "Оплата услуги в салоне красоты", order_id)
        if payment_url:
            await callback.message.edit_text(
                f"{summary}Оплатите по ссылке: {payment_url}\nПосле оплаты запись будет подтверждена.",
                reply_markup=None
            )
            await state.update_data(order_id=order_id)
            asyncio.create_task(simulate_payment_success(callback.bot, callback.from_user.id, order_id, state))
        else:
            await callback.message.edit_text("Ошибка генерации ссылки оплаты. Попробуйте позже.")
    elif payment_method == "cash":
        await callback.message.edit_text(
            f"{summary} Оплата наличными выбрана. Оплатите при посещении салона.",
            reply_markup=make_confirmation_kb()
        )
        await state.set_state(ProcReservationStates.confirming_reservation)
    await callback.answer()


async def simulate_payment_success(bot, user_id, order_id, state):
    await asyncio.sleep(5)
    await state.update_data(paid=True)
    await bot.send_message(
        chat_id=user_id,
        text="Оплата прошла успешно! Теперь подтвердите запись.",
        reply_markup=make_confirmation_kb()
    )
    await state.set_state(ProcReservationStates.confirming_reservation)


@router.callback_query(F.data == "res:confirm")
async def handle_res_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_method = data.get("payment_method")
    price = data.get("price")
    discount = data.get("discount_percent")

    if payment_method == "online" and not data.get("paid"):
        await callback.answer("Сначала оплатите услугу онлайн.")
        return

    proc = data.get("procedure")
    master = data.get("master")
    salon_id = data.get("salon")
    date = data.get("date")
    time = data.get("time")
    promo_code = data.get("promo_code")

    save_appointment(
        user_id=callback.from_user.id,
        procedure_id=proc["id"] if proc else None,
        specialist_id=master.get("id") if master else None,
        salon_id=salon_id,
        date=date,
        time=time,
        price_original=proc["prices"].get(salon_id) if proc and salon_id else None,
        discount_percent=None,
        price_final=None,
        promo_code=None,
        source="bot"
    )
    await callback.answer("Запись подтверждена")
    await callback.message.edit_text("Ваша запись подтверждена\n\n")
    await state.clear()


@router.callback_query(F.data == "res:cancel")
async def handlerescancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Запись отменена")
    await callback.message.edit_text("Запись отменена пользователем")
    await state.clear()


@router.callback_query(F.data == "pay_cash")
async def pay_cash(callback: types.CallbackQuery):
    await callback.answer()
    await state.update_data(payment_method="cash")
    try:
        await callback.message.edit_text("Оплата наличными выбрана. Оплатите при посещении салона. Спасибо!")
    except Exception:
        await callback.message.answer("Оплата наличными выбрана. Оплатите при посещении салона. Спасибо!")