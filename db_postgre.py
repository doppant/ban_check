import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

# Railway secara otomatis menyediakan DATABASE_URL
# DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = os.getenv("PUBLIC_DATABASE_URL")

def get_connection():
    # Fungsi pembantu untuk koneksi ke Postgres
    return psycopg2.connect(DATABASE_URL, sslmode='require')

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
            conn.commit()

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