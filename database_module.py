import sqlite3
import os
import pandas as pd

__default_db_path = "user_info.db"


def new_users_table(table_path: str = __default_db_path):
    """
    Creates new users database
    :param table_path: the path to the database
    :return:
    """
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        id INT PRIMARY KEY,
        username TEXT,
        subscription INTEGER,
        admin INTEGER
        )""")
    conn.commit()
    conn.close()


def get_users_info(table_path: str = __default_db_path):
    """
    Gets the info from the table
    :param table_path: the path to the database
    :return: the pandas DataFrame
    """
    conn = sqlite3.connect(table_path)
    users_info = pd.read_sql_query("""SELECT * from users""", conn)
    conn.close()
    return users_info


def get_ids_from_db(id_type: str = 'users', table_path: str = __default_db_path):
    """
    Gets the ids from database. Depends on id_type
    :param id_type: 'users' | 'admin' | 'subscription'
    :param table_path: the path to the database
    :return: the list of users ids
    """
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    print(id_type)
    if id_type == 'users':
        request = """SELECT id from users;"""
    else:
        request = f"""SELECT id from users WHERE {id_type} = 1"""
    cursor.execute(request)
    ids = []
    for user_id in cursor.fetchall():
        ids.append(user_id[0])
    conn.commit()
    conn.close()
    return ids


def get_user_id_name_from_db(id_type: str = 'users', table_path: str = __default_db_path):
    """
    Gets the users id and username from the database
    :param id_type: 'users' | 'admin' | 'subscription'
    :param table_path: the path to the database
    :return: the list of users ids and usernames
    """
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    if id_type == 'users':
        request = """SELECT id, username from users;"""
    else:
        request = f"""SELECT id, username from users WHERE {id_type} = 1"""
    cursor.execute(request)
    info = []
    for user_id, username in cursor.fetchall():
        info.append((user_id, username))
    conn.commit()
    conn.close()
    return info


def change_user_mode(change_type: str, user_id: int, value: int, table_path: str = __default_db_path):
    """
    Changes the admin or subscription mode on/off
    :param change_type: admin or subscription
    :param user_id: id
    :param value: on=1, off=0
    :param table_path: the path to the database
    :return:
    """
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""UPDATE users SET {change_type}  = {value} WHERE id = {user_id}""")
    conn.commit()
    conn.close()


def is_user_subscribed(user_id, table_path: str = __default_db_path) -> bool:
    """
    Cheks if the user subscribed or not
    :param user_id: id
    :param table_path: the path to the database
    :return: True or False
    """
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""SELECT subscription from users WHERE id = {user_id}""")
    subscribed = cursor.fetchall()
    if not subscribed:
        is_subscribed = False
    else:
        is_subscribed = bool(subscribed[0][0])
    conn.close()
    return is_subscribed


def new_user(user_id: int, username: str, table_path: str = __default_db_path):
    """
    Adds a new user to the database
    :param user_id: id
    :param username: name
    :param table_path: the path to the database
    :return:
    """
    if not os.path.exists(table_path):
        new_users_table(table_path)
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""INSERT OR IGNORE INTO users (id, username, subscription, admin) VALUES ({user_id}, "{username}", 
                                                                                                        {0},{0});""")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print(get_user_id_name_from_db())


