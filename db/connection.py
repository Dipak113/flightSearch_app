"""MySQL connection helpers shared by the CLI and Streamlit front ends."""
from contextlib import contextmanager

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract

from config import DB_CONFIG


def connect_database() -> MySQLConnectionAbstract | None:
    """Connect to the MySQL database, returning None on failure."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error:
        return None


@contextmanager
def db_cursor(connection: MySQLConnectionAbstract, commit: bool = False):
    """Yield a cursor for `connection`, committing and closing it afterwards."""
    cursor = connection.cursor()
    try:
        yield cursor
        if commit:
            connection.commit()
    finally:
        cursor.close()
