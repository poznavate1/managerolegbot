import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера   
bot = Bot(token=BOT_TOKEN, parse_mode=None)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры (админский роутер должен быть первым)
dp.include_router(admin_router)  # Сначала проверяем админские команды
dp.include_router(user_router)   # Затем пользовательские

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
 