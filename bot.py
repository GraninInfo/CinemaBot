import asyncio
import sqlite3

from aiogram import Bot, Dispatcher
from handlers import commands, text_messages

from config import BOT_TOKEN


async def main():
    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS queries('
                'userid INT,'
                'query TEXT);'
                )
    cur.execute('CREATE TABLE IF NOT EXISTS answers('
                'userid INT,'
                'title TEXT);'
                )
    conn.commit()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(commands.router, text_messages.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())