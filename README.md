# CinemaBot

This telegram bot was created as a homework assignment for Yandex School of Data Analysis.

---

The main function of this bot is as follows: you send him the name of the movie you are interested in, and the bot sends the main information about this movie as a response. CinemaBot also saves the query history for each user, it can display the user's query history, as well as clean it.

---

CinemaBot is launched using a file **bot.py**. The main functionality of it is implemented in files **commands.py** and **text_messages.py**. Before starting the bot, you need to enter your BOT TOKEN into the file **config.py**.

---

**aiogram** was used to work with the telegram API. 

To get information about the movie, the bot parses a page from the IMDb website. 

Requests are executed asynchronously using **aiohttp**. 

**sqlite3** is used to store the history of user requests.

Error messages are saved to the **py_log.log** file using **logging**.
