import os
import sqlite3
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "learnhub.db"


class DatabaseConnection:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")

        if self.database_url:
            self.backend = "postgres"
            self.connection = psycopg2.connect(
                self.database_url
            )
        else:
            self.backend = "sqlite"
            self.connection = sqlite3.connect(DATABASE)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")

    def _convert_query(self, query):
        if self.backend == "postgres":
            return query.replace("?", "%s")
        return query

    def execute(self, query, params=None):
        query = self._convert_query(query)

        if self.backend == "postgres":
            cursor = self.connection.cursor(
                cursor_factory=RealDictCursor
            )
        else:
            cursor = self.connection.cursor()

        cursor.execute(query, params or ())
        return cursor

    def cursor(self):
        if self.backend == "postgres":
            return self.connection.cursor(
                cursor_factory=RealDictCursor
            )
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

    def executescript(self, script):
        if self.backend == "sqlite":
            self.connection.executescript(script)
            return

        statements = [
            statement.strip()
            for statement in script.split(";")
            if statement.strip()
        ]

        for statement in statements:
            self.execute(statement)


def get_db_connection():
    return DatabaseConnection()