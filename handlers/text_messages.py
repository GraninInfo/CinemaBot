import sqlite3
import logging
import aiohttp

from bs4 import BeautifulSoup
from aiogram import Router
from aiogram import F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup, keyboard_button


router = Router()
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                      '537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
      }


logging.basicConfig(level=logging.WARNING, filename='py_log.log',
                    format='%(asctime)s %(levelname)s %(message)s')


def string_from_information(info: dict[str, str]) -> str:
    str_to_answer = f'<b>{info["title_and_year"]}</b>\n'

    second_line: list[str] = []
    if info['age_rating']:
        second_line += [info['age_rating']]
    if info['duration']:
        second_line += [info['duration']]
    if info['imdb_rating']:
        second_line += ['⭐ ' + info['imdb_rating'] + '/10']
    if second_line:
        str_to_answer += ' &#183; '.join(second_line) + '\n'

    if info['genres']:
        str_to_answer += f'Жанры: {info["genres"]}\n'

    if info['description']:
        str_to_answer += f'{info["description"][:-1]}\n'

    if info['poster_url']:
        str_to_answer = str_to_answer[:-1] + f'<a href="{info["poster_url"]}">.</a>'

    return str_to_answer


async def query_imdb(session: aiohttp.ClientSession, query: str) -> list[tuple[str, str]]:
    url = 'https://www.imdb.com/find/?q=' + query.replace(' ', '%20').replace(',', '%2C').replace(':', '%3A')
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            soup = BeautifulSoup(await resp.text(), "html.parser")
        else:
            logging.info('Error while requesting ' + url)
            raise Exception('Something wrong with imdb or url')

        movies = soup.find_all(class_='ipc-metadata-list-summary-item__t')
        if movies:
            result: list[tuple[str, str]] = []
            for movie in movies:
                url_to_result = 'https://www.imdb.com' + movie.get('href').split('/?')[0]
                if 'title' in url_to_result:
                    data = list(movie.parent.children)[1]
                    if len(list(data.children)) == 1:
                        title_to_result = movie.text + ' · ' + list(data.children)[0].text
                    else:
                        title_to_result = movie.text + ' · ' + list(data.children)[0].text + \
                                          ' · ' + list(data.children)[1].text
                    result.append((url_to_result, title_to_result))
            return result


async def get_information_from_imdb(session: aiohttp.ClientSession, url: str) -> dict[str, str]:
    information: dict[str, str] = {}
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            soup = BeautifulSoup(await resp.text(), "html.parser")
        else:
            logging.info('Error while requesting ' + url)
            raise Exception('Something wrong with url or imdb or url')

        for element in soup.find_all('meta'):
            if element.get('name') == 'description':
                counter = 0
                ind = 0
                for word in element.get('content').split():
                    if word[-1] == '.' and len(word) > 2:
                        counter += 1
                        if counter == 2:
                            break
                    ind += 1
                try:
                    information['description'] = ' '.join(element.get('content').split()[ind + 1:])
                except LookupError:
                    logging.error('Error while parsing description from ' + url)

            if element.get('property') == 'og:url':
                information['url'] = element.get('content')

            if element.get('property') == 'og:title':
                try:
                    if '⭐' in element.get('content'):
                        information['title_and_year'] = element.get('content').split(' ⭐')[0]
                        information['imdb_rating'] = (element.get('content').split('⭐ ')[1]).split(' |')[0]
                        information['genres'] = element.get('content').split('| ')[1]
                    else:
                        information['title_and_year'] = element.get('content').split(' | ')[0]
                        information['genres'] = element.get('content').split(' | ')[1]
                except LookupError:
                    logging.error('Error while parsing og:title from ' + url)

            if element.get('property') == 'og:description':
                try:
                    information['duration'] = element.get('content').split(' | ')[0]
                    if len(element.get('content').split(' | ')) > 1:
                        information['age_rating'] = element.get('content').split(' | ')[1]
                except LookupError:
                    logging.error('Error while parsing og:description from ' + url)

            if element.get('property') == 'og:type':
                information['type'] = element.get('content')
            if element.get('property') == 'og:image':
                information['poster_url'] = element.get('content')

        return information


@router.callback_query(F.data.startswith('movie_button_url='))
async def answer_to_query(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        url = callback.data[17:]
        info = await get_information_from_imdb(session, url)
        string_to_answer = string_from_information(info)

        conn = sqlite3.connect('CinemaBot.db')
        cur = conn.cursor()
        request = (callback.from_user.id, info['title_and_year'])
        cur.execute("INSERT INTO answers VALUES(?, ?);", request)
        conn.commit()

        await callback.message.answer(string_to_answer, parse_mode="HTML")


@router.message(F.text)
async def get_movie_info(message: Message) -> None:
    async with aiohttp.ClientSession() as session:
        conn = sqlite3.connect('CinemaBot.db')
        cur = conn.cursor()

        urls_and_titles = await query_imdb(session, message.text)
        if not urls_and_titles:
            request = (message.from_user.id, message.text)
            cur.execute("INSERT INTO queries VALUES(?, ?);", request)
            conn.commit()

            await message.answer("Простите, но по этому запросу ничего не найдено.", parse_mode="HTML")
        else:
            buttons: list[keyboard_button] = []
            for url, title in urls_and_titles:
                buttons.append(
                    [InlineKeyboardButton(
                        text=title,
                        callback_data='movie_button_url=' + url)]
                )
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            request = (message.from_user.id, message.text)
            cur.execute("INSERT INTO queries VALUES(?, ?);", request)
            conn.commit()

            await message.answer('По вашему запросу найдены следующие фильмы, пожалуйста, выберите интересующий вас:',
                                 parse_mode="HTML", reply_markup=keyboard)
