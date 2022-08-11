import sqlite3
import os

__default_db_path = "user_info.db"

def new_users_table(table_path: str = __default_db_path):
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        id INT PRIMARY KEY,
        authorized INTEGER
        )""")
    conn.commit()
    conn.close()

def get_users_ids(table_path: str = __default_db_path):
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT id from users;""")
    users = cursor.fetchall()
    conn.close()
    return users


def new_user(user_id: int, table_path: str = __default_db_path):
    if not os.path.exists(table_path):
        new_users_table(table_path)
    conn = sqlite3.connect(table_path)
    cursor = conn.cursor()
    cursor.execute(f"""INSERT OR IGNORE INTO users (id, authorized) VALUES ({user_id},{0});""")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print(get_users_ids())

