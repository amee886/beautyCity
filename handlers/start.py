from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import main_menu_kb


router = Router()


@router.message(Command("start"))
async def start_bot(message: types.Message):
    await message.answer(
        f"{message.from_user.full_name}, Вас приветствует салон красоты \"BeautyCity\"!\nВыберите нужное меню снизу",
        reply_markup=main_menu_kb()
    )