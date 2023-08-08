import asyncio
import sqlite3
from aiogram import Bot, Dispatcher
from handlers import commands, text_messages

from config import BOT_TOKEN


async def main():
    conn = sqlite3.connect('requests.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS requests('
                'userid INT,'
                'title TEXT,'
                'query TEXT);'
                )
    conn.commit()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(commands.router, text_messages.router)

    # Альтернативный вариант регистрации роутеров по одному на строку
    # dp.include_router(questions.router)
    # dp.include_router(different_types.router)

    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если у вас поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())