import requests
import sqlite3

from bs4 import BeautifulSoup
from aiogram import Router
from aiogram import F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup


router = Router()
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                      '537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
      }


def query_imdb(query: str):
    url = 'https://www.imdb.com/find/?q=' + query.replace(' ', '%20').replace(',', '%2C').replace(':', '%3A')
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
    else:
        raise Exception('Something wrong with imdb')

    movies = soup.find_all(class_='ipc-metadata-list-summary-item__t')
    if movies:
        result = []
        for movie in movies:
            result.append('https://www.imdb.com' + movie.get('href'))
        return result


def get_information_from_imdb(url: str):
    information = {}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
    else:
        raise Exception('Something wrong with url or imdb')

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
            information['description'] = ' '.join(element.get('content').split()[ind + 1:])
        if element.get('property') == 'og:url':
            information['url'] = element.get('content')
        if element.get('property') == 'og:title':
            information['title_and_year'] = element.get('content').split(' ⭐')[0]
            information['imdb_rating'] = (element.get('content').split('⭐ ')[1]).split(' |')[0]
            information['genres'] = element.get('content').split('| ')[1]
        if element.get('property') == 'og:description':
            information['duration'] = element.get('content').split(' | ')[0]
            information['age_rating'] = element.get('content').split(' | ')[1]
        if element.get('property') == 'og:type':
            information['type'] = element.get('content')
        if element.get('property') == 'og:image':
            information['poster_url'] = element.get('content')

    return information


@router.callback_query(F.data.startswith('movie_button_url='))
async def send_random_value(callback: CallbackQuery):
    url = callback.data[17:]
    movie_info = get_information_from_imdb(url)

    string_to_answer = f"<b>{movie_info['title_and_year']}</b>\n" \
                       f"{movie_info['age_rating']} &#183; {movie_info['duration']} " \
                       f"&#183; ⭐ {movie_info['imdb_rating']}/10\n" \
                       f"Жанры: {movie_info['genres']}\n" \
                       f"{movie_info['description'][:-1]}" \
                       f"<a href='{movie_info['poster_url']}'>.</a>"

    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()
    request = (callback.from_user.id, movie_info['title_and_year'])
    cur.execute("INSERT INTO answers VALUES(?, ?);", request)
    conn.commit()

    await callback.message.answer(string_to_answer, parse_mode="HTML")


@router.message(F.text)
async def movie_info(message: Message):
    conn = sqlite3.connect('CinemaBot.db')
    cur = conn.cursor()

    urls = query_imdb(message.text)
    if not urls:
        request = (message.from_user.id, 'фильм не найден', message.text)
        cur.execute("INSERT INTO requests VALUES(?, ?, ?);", request)
        conn.commit()

        await message.answer("Простите, но по этому запросу ничего не найдено.", parse_mode="HTML")
    else:
        movies_info = []
        for url in urls:
            movies_info.append(get_information_from_imdb(url))

        buttons = []
        for info in movies_info:
            buttons.append(
                [InlineKeyboardButton(
                    text=info['title_and_year'],
                    callback_data='movie_button_url=' + info['url'])]
            )
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        request = (message.from_user.id, message.text)
        cur.execute("INSERT INTO queries VALUES(?, ?);", request)
        conn.commit()

        await message.answer('По вашему запросу найдены следующие фильмы, пожалуйста, выберите интересующий вас:',
                             parse_mode="HTML", reply_markup=keyboard)
