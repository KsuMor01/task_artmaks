import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor
import aioschedule

import reviews_parser
import database_module

with open('config.txt', 'r') as f:
    lines = f.readlines()

API_TOKEN = lines[1]

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)


def get_users():
    users = database_module.get_users_ids()
    for user in users:
        yield user[0]

def form_message(new_reviews: list[dict]) -> str:
    message = "New reviews: \n"
    for review in new_reviews:
        for key, value in review.items():
            message += key + ' ' + value + '\n'
    return message


async def send_review():
    pages = reviews_parser.search_for_vit_pages()
    mes_json = reviews_parser.get_new_vit_reviews(pages)
    for user in get_users():
        await bot.send_message(chat_id=user, text=form_message(mes_json))


async def say_hello():
    for user in get_users():
        await bot.send_message(chat_id=user, text='HELLO')


@dp.message_handler(commands=['users'])
async def show_users(message: types.Message):
    mes = ''
    for i in get_users():
        mes += str(i) + ' '
    await bot.send_message(chat_id=message.chat.id, text=mes)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    database_module.new_user(user_id=message.chat.id)
    await bot.send_message(chat_id=message.chat.id, text=f"""welcome {message.chat.id}""")


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_message = """
        Hello! I am artmaksbot!
        I will send you new reviews on Vkusno i tochka every day at 12:00 AM 
        
        commands:
            /start to start 
            /users 
            /help to show this message
    """
    await bot.send_message(chat_id=message.chat.id, text=help_message)


async def scheduler():
    # aioschedule.every(1).day.at("12:00").do(send_review)
    aioschedule.every(1).minutes.do(send_review)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dp):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(on_startup=on_startup, dispatcher=dp)

