from aiogram import types
from aiogram import Router

router = Router()

@router.message()
async def echo(message: types.Message):
    if message.text == "📋 Помощь":
        await message.answer("Это раздел помощи")
    elif message.text == "ℹ️ О боте":
        await message.answer("🤖 Это тестовый бот на aiogram 3.x")
    elif message.text == 'В начало':
        pass
    else:
        await message.answer(f"Вы написали: {message.text}")