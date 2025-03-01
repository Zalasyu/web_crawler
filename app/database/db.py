import sqlite3

DATABASE_FILE = "ecfr.db"

class RegulationDAO:
    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        return self.conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

    def create_tables(self):
        with self as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    version TEXT,
                    date TEXT,
                    hash TEXT,
                    content TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    version TEXT,
                    date TEXT,
                    previous_hash TEXT,
                    new_hash TEXT
                )
            """)

    def insert_regulation(self, title, version, date, hash_value, content):
        with self as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO regulations (title, version, date, hash, content)
                VALUES (?, ?, ?, ?, ?)
            """, (title, version, date, hash_value, content))

    def get_regulation_hash(self, title, version):
        with self as cursor:
            cursor.execute("""
                SELECT hash FROM regulations WHERE title = ? AND version = ?
            """, (title, version))
            result = cursor.fetchone()
            return result[0] if result else None

    def insert_change(self, title, version, date, previous_hash, new_hash):
        with self as cursor:
            cursor.execute("""
                INSERT INTO changes (title, version, date, previous_hash, new_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (title, version, date, previous_hash, new_hash))