import sqlite3
from typing import Optional, List, Tuple

DATABASE_FILE = "ecfr.db"

class RegulationDAO:
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file

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
            cursor.execute("DROP TABLE IF EXISTS regulations")
            cursor.execute("DROP TABLE IF EXISTS changes")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    section_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    section_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    old_hash TEXT,
                    new_hash TEXT
                )
            """)

    def insert_regulation(self, title: str, section_id: str, date: str, hash_value: str, content: str):
        with self as cursor:
            cursor.execute("""
                INSERT INTO regulations (title, section_id, date, hash, content)
                VALUES (?, ?, ?, ?, ?)
            """, (title, section_id, date, hash_value, content))

    def get_regulation_hash(self, title: str, section_id: str, date: str = None) -> Optional[str]:
        with self as cursor:
            query = "SELECT hash FROM regulations WHERE title = ? AND section_id = ?"
            params = [title, section_id]
            if date:
                query += " AND date < ? ORDER BY date DESC LIMIT 1"
                params.append(date)
            else:
                query += " ORDER BY date DESC LIMIT 1"
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None

    def insert_change(self, title: str, section_id: str, date: str, old_hash: str, new_hash: str):
        with self as cursor:
            cursor.execute("""
                INSERT INTO changes (title, section_id, date, old_hash, new_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (title, section_id, date, old_hash, new_hash))

    def get_regulations(self) -> List[Tuple]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM regulations")
            return cursor.fetchall()