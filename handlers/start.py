from aiogram import types, Router
from aiogram.filters import Command
from keyboards import get_main_menu
from keyboards import get_inline_keyboard


router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Приветствие",
        reply_markup=get_main_menu(),  # Если есть основное меню
    )

    await message.answer(
        text='С чего начнём?',
        reply_markup=get_inline_keyboard(),
    )