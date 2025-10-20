import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from data.database import create_table
from handlers.quiz import router

logging.basicConfig(level=logging.INFO)

async def main():
    await create_table()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())