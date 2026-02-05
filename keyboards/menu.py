from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="О нас")],
            [
                KeyboardButton(text="Запись по процедуре"),
                KeyboardButton(text="Запись по салону")
            ],
			[
				KeyboardButton(text="Запись к мастеру"),
				KeyboardButton(text="Запись по телефону")
			]
			],
			resize_keyboard=True,
	)