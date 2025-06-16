import sqlite3

DB_NAME = "videofetcher.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                poster_url TEXT,
                user_note TEXT
            )
        """
        )
        self.conn.commit()

    def add_favorite(self, id_, title, description, poster_url, user_note):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO favorites (id, title, description, poster_url, user_note)
            VALUES (?, ?, ?, ?, ?)
        """,
            (id_, title, description, poster_url, user_note),
        )
        self.conn.commit()

    def get_favorites(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, title, description, poster_url, user_note FROM favorites"
        )
        return cursor.fetchall()

    def remove_favorite(self, id_):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE id = ?", (id_,))
        self.conn.commit()
