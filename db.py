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

def get_all_with_users():
    import sqlite3
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT discord_name, input_name FROM searches")
    rows = cursor.fetchall()

    conn.close()
    return rows  # list of tuples (discord_name, name)

def get_all_grouped():
    import sqlite3
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT discord_name, input_name FROM searches")
    rows = cursor.fetchall()

    conn.close()

    data = {}
    for user, name in rows:
        if user not in data:
            data[user] = []
        data[user].append(name)

    return data

def delete_name(discord_id, name_to_delete):
    import sqlite3
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # hapus hanya jika discord_id cocok
    cursor.execute("DELETE FROM searches WHERE discord_id = ? AND input_name = ?", (discord_id, name_to_delete))
    conn.commit()
    deleted = cursor.rowcount  # jumlah row yang dihapus
    conn.close()
    return deleted