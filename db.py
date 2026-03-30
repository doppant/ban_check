import sqlite3

DB_NAME = "data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id TEXT,
        discord_name TEXT,
        input_name TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_search(discord_id, discord_name, input_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO searches (discord_id, discord_name, input_name) VALUES (?, ?, ?)",
        (discord_id, discord_name, input_name)
    )

    conn.commit()
    conn.close()


def get_all_names():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT input_name FROM searches")
    rows = cursor.fetchall()

    conn.close()

    return [r[0] for r in rows]