import sqlite3

def connect():
    try:
        sqlite_connection = sqlite3.connect('db.db')
        cursor = sqlite_connection.cursor()
        print("Подключено к базе данных")
        return [sqlite_connection, cursor]
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)

def start():
    db = connect()

    try:
        sqlite_connection = db[0]
        cursor = db[1]

        cursor.execute('''CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY,
            admin_id INTEGER,
            title TEXT,
            desc TEXT,
            school TEXT,
            contacts TEXT)
        ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY,
            community INTEGER,
            member_id INTEGER)
        ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            tgid INTEGER PRIMARY KEY,
            desc TEXT,
            name TEXT,
            reputation INTEGER,
            last_reput INTEGER,
            interests TEXT,
            school TEXT
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY,
            secret TEXT,
            community INTEGER
        )''')

        sqlite_connection.commit()
        print("Таблица SQLite создана")

        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
