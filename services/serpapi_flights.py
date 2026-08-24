"""Live flight search via SerpAPI's Google Flights engine, cached in MongoDB."""
from datetime import datetime, timezone

import requests

from config import SERPAPI_KEY
from db.mongo import get_cache_collection

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


class SerpApiError(Exception):
    """Raised when SerpAPI is unreachable, misconfigured, or returns an error."""


def _cache_key(source_iata: str, destination_iata: str, travel_date: str) -> str:
    return f"{source_iata.upper()}-{destination_iata.upper()}-{travel_date}"


def _parse_flight_options(data: dict) -> list[dict]:
    """Flatten SerpAPI's best_flights/other_flights (each a list of legs) into one row per option."""
    options = []
    for bucket in ("best_flights", "other_flights"):
        for option in data.get(bucket, []):
            legs = option.get("flights", [])
            if not legs:
                continue

            first_leg, last_leg = legs[0], legs[-1]
            airlines = ", ".join(dict.fromkeys(leg.get("airline", "") for leg in legs if leg.get("airline")))

            options.append({
                "airline": airlines or "Unknown",
                "departure_airport": first_leg.get("departure_airport", {}).get("id", ""),
                "arrival_airport": last_leg.get("arrival_airport", {}).get("id", ""),
                "departure_time": first_leg.get("departure_airport", {}).get("time", ""),
                "arrival_time": last_leg.get("arrival_airport", {}).get("time", ""),
                "duration_minutes": option.get("total_duration") or sum(leg.get("duration", 0) for leg in legs),
                "price": option.get("price"),
                "stops": len(legs) - 1,
            })
    return options


def search_flights(
    source_iata: str, destination_iata: str, travel_date: str, use_cache: bool = True
) -> tuple[list[dict], bool]:
    """Search live flights for a route+date. Returns (flight options, served_from_cache)."""
    if not SERPAPI_KEY:
        raise SerpApiError("SERPAPI_KEY is not set. Add it to your .env file.")

    key = _cache_key(source_iata, destination_iata, travel_date)
    cache = get_cache_collection() if use_cache else None

    if cache is not None:
        cached = cache.find_one({"_id": key})
        if cached is not None:
            return _parse_flight_options(cached["raw_response"]), True

    params = {
        "engine": "google_flights",
        "departure_id": source_iata.upper(),
        "arrival_id": destination_iata.upper(),
        "outbound_date": travel_date,
        "type": "2",  # one-way
        "currency": "INR",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=15)
    except requests.RequestException:
        # Don't surface the exception text: it can embed the request URL, api_key included.
        raise SerpApiError("Could not reach SerpAPI. Check your network connection and try again.")

    try:
        data = response.json()
    except ValueError:
        raise SerpApiError(f"SerpAPI returned an unexpected response (HTTP {response.status_code}).")

    if response.status_code != 200 or data.get("error"):
        raise SerpApiError(data.get("error", f"SerpAPI request failed (HTTP {response.status_code})."))

    if cache is not None:
        cache.replace_one(
            {"_id": key},
            {
                "_id": key,
                "source": source_iata.upper(),
                "destination": destination_iata.upper(),
                "travel_date": travel_date,
                "raw_response": data,
                "cached_at": datetime.now(timezone.utc),
            },
            upsert=True,
        )

    return _parse_flight_options(data), False
