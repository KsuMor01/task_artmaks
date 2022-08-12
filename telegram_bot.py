import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData
import aioschedule

import reviews_parser
import database_module

with open('config.txt', 'r') as f:
    lines = f.readlines()

API_TOKEN = lines[1]

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

cb = CallbackData('post', 'action', 'user_id')


def get_users():
    for user_id in database_module.get_users_ids():
        yield user_id


def get_admins():
    for admin_id in database_module.get_admins_ids():
        yield admin_id


def form_message(new_reviews: list[dict]) -> str:
    message = "New reviews: \n"
    # TODO: beautiful format
    for review in new_reviews:
        for key, value in review.items():
            message += key + ' ' + value + '\n'
    return message


async def send_review():
    pages = reviews_parser.search_for_vit_pages()
    mes_json = reviews_parser.get_new_vit_reviews(pages)
    for user in get_users():
        await bot.send_message(chat_id=user, text=form_message(mes_json))


@dp.message_handler(commands=['review'])
async def subscribe(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    if database_module.is_user_subscribed(message.chat.id):
        mes = """
            Вы уже подписаны. Хотите отписаться?
        """
        keyboard.add(types.InlineKeyboardButton(text="отписаться",
                                                callback_data=cb.new(action="unsubscribe", user_id=message.chat.id)))
        keyboard.add(types.InlineKeyboardButton(text="отмена",
                                                callback_data=cb.new(action="cancel", user_id=message.chat.id)))

    else:
        mes = """
            Вы еще не подписаны. Хотите подписаться на рассылку?
        """
        keyboard.add(types.InlineKeyboardButton(text="подписаться",
                                                callback_data=cb.new(action="subscribe", user_id=message.chat.id)))
        keyboard.add(types.InlineKeyboardButton(text="отмена",
                                                callback_data=cb.new(action="cancel", user_id=message.chat.id)))

    await message.answer(mes, reply_markup=keyboard)


@dp.callback_query_handler(cb.filter(action="cancel"))
async def want_to_subscribe(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.from_user.id, text="отмена")


@dp.callback_query_handler(cb.filter(action="cancel_sub_request"))
async def want_to_subscribe(call: types.CallbackQuery, callback_data: dict):
    await bot.send_message(chat_id=call.from_user.id, text="отмена запроса")
    await bot.send_message(chat_id=callback_data['user_id'], text="К сожалению, запрос не был одобрен админом")


@dp.callback_query_handler(cb.filter(action="unsubscribe"))
async def want_to_subscribe(call: types.CallbackQuery, callback_data: dict):
    await call.message.answer("Направляю запрос на отмену подписки админу.", reply_markup=types.ReplyKeyboardRemove())
    text = f"""
        Пользователь {call.message.chat.username} ({call.message.chat.id}) хочет отписаться от рассылки. 
        Отменить подписку?
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="отменить",
                                            callback_data=cb.new(action="sub_off",
                                                                 user_id=callback_data['user_id'])))
    keyboard.add(types.InlineKeyboardButton
                 (text="запретить",
                  callback_data=cb.new(action="cancel_sub_request", user_id=callback_data['user_id'])))

    for admin in get_admins():
        await bot.send_message(chat_id=admin, text=text, reply_markup=keyboard)


@dp.callback_query_handler(cb.filter(action="subscribe"))
async def want_to_subscribe(call: types.CallbackQuery, callback_data: dict):
    await call.message.answer("Направляю запрос на подписку админу.", reply_markup=types.ReplyKeyboardRemove())
    text = f"""
        Пользователь {call.message.chat.username} ({call.message.chat.id}) хочет подписаться на рассылку. 
        Разрешить подписку?
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="разрешить", callback_data=cb.new(action="sub_on",
                                                                                   user_id=callback_data['user_id'])))
    keyboard.add(types.InlineKeyboardButton(text="запретить", callback_data=cb.new(action="cancel_sub_request",
                                                                                   user_id=callback_data['user_id'])))

    for admin in get_admins():
        await bot.send_message(chat_id=admin, text=text, reply_markup=keyboard)


@dp.callback_query_handler(cb.filter(action="sub_off"))
async def subscribe_on(call: types.CallbackQuery, callback_data: dict):
    database_module.change_subscription(callback_data['user_id'], 0)
    text = 'Вы были отписаны от рассылки'

    await bot.send_message(chat_id=callback_data['user_id'], text=text)
    await bot.send_message(chat_id=call.message.chat.id, text="Подписка отменена")


@dp.callback_query_handler(cb.filter(action="sub_on"))
async def subscribe_on(call: types.CallbackQuery, callback_data: dict):
    database_module.change_subscription(callback_data['user_id'], 1)
    text = 'Вы были подписаны на рассылку'

    await bot.send_message(chat_id=callback_data['user_id'], text=text)
    await bot.send_message(chat_id=call.message.chat.id, text="Подписка оформлена")


async def say_hello():
    for user in get_users():
        await bot.send_message(chat_id=user, text='HELLO')


@dp.message_handler(lambda message: message.chat.id in get_admins(), commands=['users'])
async def show_users(message: types.Message):
    mes = ''
    print(get_admins())
    for i in get_users():
        mes += str(i) + ' '
    await bot.send_message(chat_id=message.chat.id, text=mes)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    database_module.new_user(user_id=message.chat.id)
    await bot.send_message(chat_id=message.chat.id, text=f"""welcome {message.chat.username}""")


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_message = """
        Привет! Я artmaksbot.
        Я делаю рассылку новых отзывов о ресторане Вкусно и точка каждый день в 12:00 утра.
        
        Напиши команду /review чтобы подписаться на рассылку
        
        Другие команды:
            /start начать работу
            /review подписаться на рассылку
            /help to show this message           
    """

    if message.chat.id in database_module.get_admins_ids():
        help_message += """
            Только для администраторов:
            /users выводит информацию о пользователях
        """
    await bot.send_message(chat_id=message.chat.id, text=help_message)


async def scheduler():
    # aioschedule.every(1).day.at("12:00").do(send_review)
    aioschedule.every(10).minutes.do(send_review)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dp):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(on_startup=on_startup, dispatcher=dp)
