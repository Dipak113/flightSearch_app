"""Data access for the `searches` table, mirrored into MongoDB's flight_app.searches."""
from datetime import datetime, timezone

from db.connection import db_cursor
from db.mongo import get_app_collection


class InvalidSearch(Exception):
    """Raised when search input fails validation."""


def _validate(source_id: int, destination_id: int, travel_date: str) -> None:
    if source_id == destination_id:
        raise InvalidSearch("Source and destination cannot be the same.")
    try:
        datetime.strptime(travel_date, "%Y-%m-%d")
    except ValueError:
        raise InvalidSearch("Invalid date format! Use YYYY-MM-DD.")


def create_search(connection, source_id: int, destination_id: int, travel_date: str) -> int:
    _validate(source_id, destination_id, travel_date)

    with db_cursor(connection, commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO searches (source_airport_id, destination_airport_id, travel_date)
            VALUES (%s, %s, %s)
            """,
            (source_id, destination_id, travel_date),
        )
        search_id = cursor.lastrowid

    _mirror_search(search_id, source_id, destination_id, travel_date)
    return search_id


def get_searches(connection) -> list[tuple]:
    with db_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT
                s.search_id,
                a1.iata_code AS source,
                a2.iata_code AS destination,
                s.travel_date,
                s.search_timestamp
            FROM searches s
            JOIN airports a1 ON s.source_airport_id = a1.airport_id
            JOIN airports a2 ON s.destination_airport_id = a2.airport_id
            ORDER BY s.search_id DESC
            """
        )
        return cursor.fetchall()


def delete_search(connection, search_id: int) -> bool:
    with db_cursor(connection, commit=True) as cursor:
        cursor.execute("DELETE FROM flights WHERE search_id = %s", (search_id,))
        cursor.execute("DELETE FROM searches WHERE search_id = %s", (search_id,))
        deleted = cursor.rowcount > 0

    if deleted:
        _mirror_delete_search(search_id)
    return deleted


def _mirror_search(search_id: int, source_id: int, destination_id: int, travel_date: str) -> None:
    """Best-effort: MySQL is the source of truth, Mongo mirroring must never break a write."""
    collection = get_app_collection("searches")
    if collection is None:
        return
    collection.replace_one(
        {"_id": search_id},
        {
            "_id": search_id,
            "source_airport_id": source_id,
            "destination_airport_id": destination_id,
            "travel_date": travel_date,
            "search_timestamp": datetime.now(timezone.utc),
        },
        upsert=True,
    )


def _mirror_delete_search(search_id: int) -> None:
    searches_collection = get_app_collection("searches")
    if searches_collection is not None:
        searches_collection.delete_one({"_id": search_id})

    flights_collection = get_app_collection("flights")
    if flights_collection is not None:
        flights_collection.delete_many({"search_id": search_id})
