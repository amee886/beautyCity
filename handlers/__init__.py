from aiogram import Dispatcher
from handlers.start import router as start_router
from handlers.info import router as info_router
from handlers.procedure_reservation import router as procedure_reservation_router
from handlers.phone_reservation import router as phone_reservation_router
from handlers.salon_reservation import router as salon_reservation_router


def register_routes(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(info_router)
    dp.include_router(procedure_reservation_router)
    dp.include_router(phone_reservation_router)
    dp.include_router(salon_reservation_router)