from aiogram import F, Router, types


router = Router()


@router.message(F.text == "О нас")
async def info(message: types.Message):
	await message.answer(
		"Добро пожаловать в официальный бот записи салона \"BeautyCity\" — ваш персональный ассистент для планирования красоты и ухода.\n"
		"Оформите запись прямо сейчас и позвольте профессионалам позаботиться о вашей красоте.\n"
	)
