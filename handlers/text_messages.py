import requests
import sqlite3

from bs4 import BeautifulSoup
from aiogram import Router
from aiogram import F
from aiogram.types import Message


router = Router()
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                      '537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
      }


def query_imdb(query):
    url = 'https://www.imdb.com/find/?q=' + query.replace(' ', '%20').replace(',', '%2C').replace(':', '%3A')
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
    else:
        raise Exception('Something wrong with imdb')

    result = soup.find(class_='ipc-metadata-list-summary-item__t')
    if result:
        return 'https://www.imdb.com' + result.get('href')


def get_information_from_imdb(url):
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
        # if element.get('property') == 'og:url':
        #     information['url'] = element.get('content')
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


@router.message(F.text)
async def movie_info(message: Message):
    conn = sqlite3.connect('requests.db')
    cur = conn.cursor()

    url = query_imdb(message.text)
    if not url:
        request = (message.from_user.id, 'фильм не найден', message.text)
        cur.execute("INSERT INTO requests VALUES(?, ?, ?);", request)
        conn.commit()

        await message.answer("Простите, но по этому запросу ничего не найдено.", parse_mode="HTML")
    else:
        information = get_information_from_imdb(url)
        string_to_answer = f"<b>{information['title_and_year']}</b>\n" \
                           f"{information['age_rating']} &#183; {information['duration']} " \
                           f"&#183; ⭐ {information['imdb_rating']}/10\n" \
                           f"Жанры: {information['genres']}\n" \
                           f"{information['description'][:-1]}" \
                           f"<a href='{information['poster_url']}'>.</a>"

        request = (message.from_user.id, information['title_and_year'], message.text)
        cur.execute("INSERT INTO requests VALUES(?, ?, ?);", request)
        conn.commit()

        await message.answer(string_to_answer, parse_mode="HTML")
