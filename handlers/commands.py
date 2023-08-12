import sqlite3

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()


def case_for_number(number: int) -> str:
    if number == 1 or number > 5:
        return 'раз'
    else:
        return 'раза'


@router.message(Command('start'))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет, я CinemaBot. Я могу рассказать тебе о фильмах, а также дать ссылку для просмотра. "
        "Тебе нужно только написать мне название интересующего тебя фильма или сериала.\n"
        "Для дополнительной информации воспользуйтесь командой /help."
    )


@router.message(Command('help'))
async def cmd_start(message: Message) -> None:
    await message.answer(
        'Доступные команды:\n'
        '/help -- показать список возможных взаимодействий с ботом;\n'
        '/history -- показать последние 10 ваших запросов;\n'
        '/allhistory -- показать всю историю ваших запросов;\n'
        '/stats -- показать, информацию о каких фильмах вы получили и сколько раз;\n'
        '/clearhistory -- отчистить всю историю ваших запросов.\n'
        'Основная функция бота следующая: вы вводите название фильма или сериала, а бот'
        'присылает вам основную информацию об этом проекте, а также ссылку для просмотра(coming soon).'
    )


@router.message(Command('history'))
async def cmd_history(message: Message) -> None:
    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM queries "
                f"WHERE userid = {message.from_user.id};")
    all_results = cur.fetchall()

    if all_results:
        to_answer = 'Список ваших последних запросов(от более поздних к более ранним):\n'
        all_results.reverse()
        for request, _ in zip(all_results, range(10)):
            to_answer += f'{request[1]}\n'

        await message.answer(to_answer[:-1])
    else:
        await message.answer('В данный момент в истории ваших запросов пусто.')


@router.message(Command('allhistory'))
async def cmd_all_history(message: Message) -> None:
    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM queries "
                f"WHERE userid = {message.from_user.id};")
    all_results = cur.fetchall()

    if all_results:
        to_answer = 'Список ваших запросов(от более ранних к более поздним):\n'
        for request in all_results:
            to_answer += f'{request[1]}\n'

        await message.answer(to_answer[:-1])
    else:
        await message.answer('В данный момент в истории ваших запросов пусто.')


@router.message(Command('stats'))
async def cmd_stats(message: Message) -> None:
    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()

    cur.execute(f"SELECT title, count(title) FROM answers "
                f"WHERE userid = {message.from_user.id} "
                f"GROUP BY title "
                f"ORDER BY count(title) DESC;")
    all_results = cur.fetchall()

    if all_results:
        to_answer = 'На ваши запросы были выданы результаты в следующих количествах:\n'
        for title, count in all_results:
            to_answer += f'{count} {case_for_number(count)} -- {title},\n'
        await message.answer(to_answer[:-2])
    else:
        await message.answer('В данный момент в истории ваших запросов пусто.')


@router.message(Command('clearhistory'))
async def cmd_clear_history(message: Message) -> None:
    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()
    cur.execute(f"DELETE FROM queries WHERE userid = {message.from_user.id};")
    cur.execute(f"DELETE FROM answers WHERE userid = {message.from_user.id};")
    conn.commit()
