import sqlite3

def insert_dummy_data(dummy_data):
    with get_db() as conn:
        for user_name, desk_id, start_time, end_time in dummy_data:
            conn.execute("""
                INSERT INTO history (user_name, desk_id, start_time, end_time)
                VALUES (?, ?, ?, ?)
            """, (user_name, desk_id, start_time, end_time))
def get_db():
    conn = sqlite3.connect("lab.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS desks (
                id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                desk_id INTEGER,
                start_time TEXT,
                end_time TEXT
            )
        """)

        for i in range(1, 9):
            conn.execute(
                "INSERT OR IGNORE INTO desks (id, user_name) VALUES (?, NULL)",
                (i,)
            )