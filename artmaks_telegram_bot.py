"""
This is the telegram bot script
"""

import asyncio
import datetime
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData
import aioschedule

import reviews_parser
import database_module
import enum
from config import TOKEN


bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

cb = CallbackData('post', 'action', 'user_id')


class IdTypes(enum.Enum):
    """
    Types of ids to search in database
    """
    USERS = 'users',
    ADMINS = 'admin',
    SUBS = 'subscription'


def get_ids(id_type: IdTypes):
    for user_id in database_module.get_ids_from_db(id_type=id_type.value):
        yield user_id


def get_user_id_name(id_type: IdTypes):
    for user_id, username in database_module.get_user_id_name_from_db(id_type=id_type.value[0]):
        yield user_id, username


def form_message(review: dict) -> str:
    """
    Forms the pretty text from the dict reviews
    :param review: the dict review
    :return: the text of the message
    """
    message = ''
    d_time_format = datetime.datetime.strftime(
        datetime.datetime.strptime(review['datetime'], "%Y-%m-%dT%H:%M:%S+03:00"), "%d.%m.%Y %H:%M:%S")

    message += "Источник: " + review['url']
    message += "\nАвтор: " + review['author']
    message += "\nДата и время публикации: " + d_time_format
    message += "\nОценка: " + review['rate'] + " из 5"
    message += "\nКомментарий: " + review['text']
    return message


async def send_reviews():
    """
    Sends the reviews to the subscribed users
    :return:
    """
    pages = reviews_parser.search_for_vit_pages()
    new_reviews_json = reviews_parser.get_new_vit_reviews(pages)
    for user in get_ids(IdTypes.SUBS):
        if new_reviews_json:
            await bot.send_message(chat_id=user, text="Новые отзывы: ")
            for review in new_reviews_json:
                await bot.send_message(chat_id=user, text=form_message(review))


async def scheduler():
    """
    Sends the reviews to the users every day at 12:00
    :return:
    """
    aioschedule.every(1).minutes.do(send_reviews)
    aioschedule.every(1).day.at("12:00").do(send_reviews)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dispatcher):
    asyncio.create_task(scheduler())


@dp.message_handler(commands=['review'])
async def subscribe(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    if database_module.is_user_subscribed(message.chat.id):
        mes = """
            Вы уже подписаны. Хотите отписаться?
        """
        keyboard.add(types.InlineKeyboardButton(text="отписаться",
                                                callback_data=cb.new(action="unsubscribe", user_id=message.chat.id)))
        keyboard.add(types.InlineKeyboardButton(text='отмена',
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
async def cancel(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.from_user.id, text="отмена")


@dp.callback_query_handler(cb.filter(action="cancel_sub_request"))
async def cancel_sub_request(call: types.CallbackQuery, callback_data: dict):
    await bot.send_message(chat_id=call.from_user.id, text="отмена запроса")
    await bot.send_message(chat_id=callback_data['user_id'], text="К сожалению, запрос не был одобрен админом")


@dp.callback_query_handler(cb.filter(action="unsubscribe"))
async def want_to_unsubscribe(call: types.CallbackQuery, callback_data: dict):
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

    for admin in get_ids(IdTypes.ADMINS):
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

    for admin in get_ids(IdTypes.ADMINS):
        await bot.send_message(chat_id=admin, text=text, reply_markup=keyboard)


@dp.callback_query_handler(cb.filter(action="sub_off"))
async def subscribe_on(call: types.CallbackQuery, callback_data: dict):
    database_module.change_user_mode(IdTypes.SUBS.value, callback_data['user_id'], 0)
    text = 'Вы были отписаны от рассылки'

    await bot.send_message(chat_id=callback_data['user_id'], text=text)
    await bot.send_message(chat_id=call.message.chat.id, text="Подписка отменена")


@dp.callback_query_handler(cb.filter(action="sub_on"))
async def subscribe_on(call: types.CallbackQuery, callback_data: dict):
    database_module.change_user_mode(IdTypes.SUBS.value, callback_data['user_id'], 1)
    text = 'Вы были подписаны на рассылку'

    await bot.send_message(chat_id=callback_data['user_id'], text=text)
    await bot.send_message(chat_id=call.message.chat.id, text="Подписка оформлена")


@dp.message_handler(lambda message: message.chat.id in get_ids(IdTypes.ADMINS), commands=['users'])
async def show_users_info(message: types.Message):
    text = database_module.get_users_info().to_csv(sep='\t')
    await bot.send_message(chat_id=message.chat.id, text=text)


def message_contains_id_from_admin(message):
    if message.chat.id in get_ids(IdTypes.ADMINS) and int(message) in get_ids(IdTypes.USERS):
        return True
    else:
        return False


@dp.callback_query_handler(cb.filter(action="retire"))
async def retire(call: types.CallbackQuery, callback_data: dict):
    database_module.change_user_mode(change_type='admin', user_id=callback_data['user_id'], value=0)
    text = f"""
        Администратор {callback_data['user_id']} был разжалован.
    """
    await bot.send_message(chat_id=call.message.chat.id, text=text)
    await bot.send_message(chat_id=callback_data['user_id'], text="Вы больше не являетесь админом.")


@dp.callback_query_handler(cb.filter(action="retire_admin"))
async def retire_admin(call: types.CallbackQuery):

    keyboard = types.InlineKeyboardMarkup()
    for admin_id, admin_name in get_user_id_name(id_type=IdTypes.ADMINS):
        text = admin_name + '(' + str(admin_id) + ')'
        keyboard.add(types.InlineKeyboardButton(
            text=text, callback_data=cb.new(action='retire', user_id=admin_id)))
    text = 'Выберите администратора, которого хотите разжаловать.'
    await bot.send_message(chat_id=call.message.chat.id, text=text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith('id'))
async def new_admin(message: types.Message):
    database_module.change_user_mode(change_type='admin', user_id=int(message.text[2:]), value=1)
    text = f"""
        Пользователь {message.text} был назначен администратором.
    """
    await bot.send_message(chat_id=message.chat.id, text=text)
    await bot.send_message(chat_id=int(message.text[2:]), text="Вы были назначены администратором")


@dp.callback_query_handler(cb.filter(action="new_admin"))
async def new_admin(call: types.CallbackQuery):
    text = 'Введите id пользователя, которого хотите назначить администратором. В формате, например id123123123'
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.message_handler(lambda message: message.chat.id in get_ids(IdTypes.ADMINS), commands=['admins'])
async def manage_admins(message: types.Message):

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="назначить админа",
                                            callback_data=cb.new(action="new_admin", user_id="None")))
    keyboard.add(types.InlineKeyboardButton(text="разжаловать админа",
                                            callback_data=cb.new(action="retire_admin", user_id="None")))
    text = database_module.get_users_info().to_csv(sep='\t')
    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    database_module.new_user(user_id=message.chat.id, username=message.chat.username)
    text = f"""
        Привет, {message.chat.username}!
        Я artmaksbot.
        Я делаю рассылку новых отзывов о ресторане Вкусно и точка в Уфе каждый день в 12:00 утра.
        
        Напиши команду /review чтобы подписаться на рассылку
        
        Напиши команду /help чтобы узнать больше о моих командах.            
        
    """
    await bot.send_message(chat_id=message.chat.id, text=text)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_message = """
        Привет! Я artmaksbot.
        Я делаю рассылку новых отзывов о ресторане "Вкусно и точка" в Уфе каждый день в 12:00 утра.
        
        Напиши команду /review чтобы подписаться на рассылку
        
        Другие команды:
            /start начать работу
            /review подписаться на рассылку новых отзывов
            /help отобразить это сообщение      
    """

    if message.chat.id in database_module.get_ids_from_db(IdTypes.ADMINS.value[0]):
        help_message += """
            Только для администраторов:
            /users выводит информацию о пользователях
            /admins управлять администраторами
        """
    await bot.send_message(chat_id=message.chat.id, text=help_message)


if __name__ == '__main__':
    executor.start_polling(on_startup=on_startup, dispatcher=dp)
