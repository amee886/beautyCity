from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import main_menu_kb

from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import main_menu_kb

from aiogram.types import FSInputFile
from config import PD_PDF_PATH

router = Router()


@router.message(Command("start"))
async def start_bot(message: types.Message):
    pdf = FSInputFile(PD_PDF_PATH)

    await message.answer_document(
        document=pdf,
        caption=(
            "Перед началом работы с ботом ознакомьтесь, пожалуйста, "
            "с согласием на обработку персональных данных."
        )
    )

    await message.answer(
        f"{message.from_user.full_name}, Вас приветствует салон красоты \"BeautyCity\"!\nВыберите нужное меню снизу",
        reply_markup=main_menu_kb()
    )
