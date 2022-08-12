import sqlite3
import os

__default_db_path = "user_info.db"


def new_users_table(table_path: str = __default_db_path):
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        id INT PRIMARY KEY,
        subscription INTEGER,
        admin INTEGER
        )""")
    conn.commit()
    conn.close()


def get_users_ids(table_path: str = __default_db_path):
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT id from users;""")
    users = []
    for user in cursor.fetchall():
        users.append(user[0])
    conn.close()
    return users


def get_admins_ids(table_path: str = __default_db_path):
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT id from users WHERE admin = 1""")
    admins = []
    for admin in cursor.fetchall():
        admins.append(admin[0])
    conn.close()
    return admins


def change_subscription(user_id: int, value: int, table_path: str = __default_db_path):
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""UPDATE users SET subscription  = {value} WHERE id = {user_id}""")
    conn.commit()
    conn.close()


def is_user_subscribed(user_id, table_path: str = __default_db_path) -> bool:
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""SELECT subscription from users WHERE id = {user_id}""")
    subscribed = cursor.fetchall()
    if subscribed == []:
        is_subscribed = False
    else:
        is_subscribed = bool(subscribed[0][0])
    conn.close()
    return is_subscribed


def new_user(user_id: int, table_path: str = __default_db_path):
    if not os.path.exists(table_path):
        new_users_table(table_path)
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""INSERT OR IGNORE INTO users (id, subscription, admin) VALUES ({user_id},{0},{0});""")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print(get_users_ids())

