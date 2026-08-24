"""Data access for the `airports` table, mirrored into MongoDB's flight_app.airports."""
from mysql.connector import IntegrityError

from db.connection import db_cursor
from db.mongo import get_app_collection


class AirportAlreadyExists(Exception):
    """Raised when an airport with the given IATA code already exists."""


def add_airport(connection, iata_code: str, airport_name: str) -> int:
    iata_code = iata_code.strip().upper()
    airport_name = airport_name.strip().upper()

    try:
        with db_cursor(connection, commit=True) as cursor:
            cursor.execute(
                "INSERT INTO airports (iata_code, airport_name) VALUES (%s, %s)",
                (iata_code, airport_name),
            )
            airport_id = cursor.lastrowid
    except IntegrityError:
        raise AirportAlreadyExists(iata_code)

    _mirror_airport(airport_id, iata_code, airport_name)
    return airport_id


def get_airports(connection) -> list[tuple]:
    with db_cursor(connection) as cursor:
        cursor.execute("SELECT * FROM airports ORDER BY iata_code")
        return cursor.fetchall()


def _mirror_airport(airport_id: int, iata_code: str, airport_name: str) -> None:
    """Best-effort: MySQL is the source of truth, Mongo mirroring must never break a write."""
    collection = get_app_collection("airports")
    if collection is None:
        return
    collection.replace_one(
        {"_id": airport_id},
        {"_id": airport_id, "iata_code": iata_code, "airport_name": airport_name},
        upsert=True,
    )
