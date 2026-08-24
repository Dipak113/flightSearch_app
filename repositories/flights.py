"""Data access for the `flights` table, mirrored into MongoDB's flight_app.flights."""
from db.connection import db_cursor
from db.mongo import get_app_collection


def add_flight(
    connection,
    search_id: int,
    airline: str,
    departure_airport: str,
    arrival_airport: str,
    departure_time: str,
    arrival_time: str,
    duration_minutes: int,
    price: float,
) -> int:
    airline = airline.strip()
    departure_airport = departure_airport.strip().upper()
    arrival_airport = arrival_airport.strip().upper()

    with db_cursor(connection, commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO flights
            (search_id, airline, departure_airport, arrival_airport,
             departure_time, arrival_time, duration_minutes, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                search_id, airline, departure_airport, arrival_airport,
                departure_time, arrival_time, duration_minutes, price,
            ),
        )
        flight_id = cursor.lastrowid

    _mirror_flight(
        flight_id, search_id, airline, departure_airport, arrival_airport,
        departure_time, arrival_time, duration_minutes, price,
    )
    return flight_id


def get_flights_by_search(connection, search_id: int) -> list[tuple]:
    with db_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT flight_id, airline, departure_airport, arrival_airport,
                   departure_time, arrival_time, duration_minutes, price
            FROM flights
            WHERE search_id = %s
            ORDER BY price
            """,
            (search_id,),
        )
        return cursor.fetchall()


def get_all_flights(connection) -> list[tuple]:
    with db_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT f.flight_id, f.airline, f.departure_airport, f.arrival_airport,
                   f.departure_time, f.arrival_time, f.duration_minutes, f.price, f.search_id
            FROM flights f
            ORDER BY f.search_id, f.price
            """
        )
        return cursor.fetchall()


def _mirror_flight(
    flight_id: int, search_id: int, airline: str, departure_airport: str, arrival_airport: str,
    departure_time: str, arrival_time: str, duration_minutes: int, price: float,
) -> None:
    """Best-effort: MySQL is the source of truth, Mongo mirroring must never break a write."""
    collection = get_app_collection("flights")
    if collection is None:
        return
    collection.replace_one(
        {"_id": flight_id},
        {
            "_id": flight_id,
            "search_id": search_id,
            "airline": airline,
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration_minutes": duration_minutes,
            "price": price,
        },
        upsert=True,
    )
