import os
from dotenv import load_dotenv

load_dotenv()
import sqlite3
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
import mysql.connector


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "learnhub.db"


class DatabaseConnection:

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")

        # 1. Render / PostgreSQL
        if self.database_url:
            self.backend = "postgres"

            self.connection = psycopg2.connect(
                self.database_url
            )

        # 2. Local MySQL
        elif os.getenv("DB_HOST"):
            self.backend = "mysql"

            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                port=int(os.getenv("DB_PORT", 3306)),
                ssl_disabled=False
            )
            

        # 3. Local SQLite fallback
        else:
            self.backend = "sqlite"

            self.connection = sqlite3.connect(
                DATABASE
            )

            self.connection.row_factory = sqlite3.Row

            self.connection.execute(
                "PRAGMA foreign_keys = ON"
            )

    def _convert_query(self, query):

        if self.backend in ("postgres", "mysql"):
            return query.replace("?", "%s")

        return query

    def execute(self, query, params=None):
        query = self._convert_query(query)

        if self.backend == "postgres":
            cursor = self.connection.cursor(
                cursor_factory=RealDictCursor
            )

        elif self.backend == "mysql":
            cursor = self.connection.cursor(
                dictionary=True
            )

        else:
            cursor = self.connection.cursor()

        cursor.execute(
            query,
            params or ()
        )

        return cursor

    def cursor(self):
        if self.backend == "postgres":
            return self.connection.cursor(
                cursor_factory=RealDictCursor
            )

        elif self.backend == "mysql":
            return self.connection.cursor(
                dictionary=True
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