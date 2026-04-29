import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL = {
#                     "host": os.getenv("DB_HOST"),
#                     "database": os.getenv("DB_NAME"),
#                     "user": os.getenv("DB_USER"),
#                     "password": os.getenv("DB_PASSWORD"),
#                     "port": os.getenv("DB_PORT", "5432")

#                 }

def get_connection():
    # Fungsi pembantu untuk koneksi ke Postgres
    return psycopg2.connect(DATABASE_URL, sslmode='require')
    # return psycopg2.connect(**DATABASE_URL)
    

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id SERIAL PRIMARY KEY,
                discord_id TEXT,
                discord_name TEXT,
                input_name TEXT,
                UNIQUE(discord_id, input_name)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_state (
                id INTEGER PRIMARY KEY DEFAULT 1,
                last_article_id TEXT
            )
            """)

            # check row
            cursor.execute("""
            INSERT INTO web_state (id, last_article_id)
            VALUES (1, NULL)
            ON CONFLICT (id) DO NOTHING
            """)

            conn.commit()

# =========================
# USERS FUNCTIONS
# =========================

def save_search(discord_id, discord_name, input_name):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # ON CONFLICT agar tidak error jika data duplikat (karena UNIQUE constraint)
            cursor.execute(
                "INSERT INTO searches (discord_id, discord_name, input_name) VALUES (%s, %s, %s) "
                "ON CONFLICT (discord_id, input_name) DO NOTHING",
                (discord_id, discord_name, input_name)
            )
            conn.commit()

def get_all_with_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT discord_name, input_name FROM searches")
            return cursor.fetchall()

def get_all_grouped():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT discord_name, input_name FROM searches")
            rows = cursor.fetchall()
            
            data = {}
            for user, name in rows:
                if user not in data:
                    data[user] = []
                data[user].append(name)
            return data

def delete_name(discord_id, name_to_delete):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM searches WHERE discord_id = %s AND input_name = %s", 
                (discord_id, name_to_delete)
            )
            conn.commit()
            return cursor.rowcount
        
def update_name(discord_id, old_name, new_name):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE searches
                SET input_name = %s
                WHERE discord_id = %s AND input_name = %s
                """,
                (new_name, discord_id, old_name)
            )
            conn.commit()
            return cursor.rowcount

# =========================
# WEB STATE FUNCTIONS
# =========================

def get_last_article_id():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT last_article_id FROM web_state WHERE id = 1")
            result = cursor.fetchone()
            return result[0] if result else None


def update_last_article(article_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE web_state
                SET last_article_id = %s
                WHERE id = 1
                """,
                (article_id,)
            )
            conn.commit()