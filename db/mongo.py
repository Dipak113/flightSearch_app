"""MongoDB connection, used both to cache raw SerpAPI responses and to mirror MySQL writes."""
from pymongo import MongoClient
from pymongo.collection import Collection

from config import MONGO_APP_DB_NAME, MONGO_CACHE_TTL_SECONDS, MONGO_DB_NAME, MONGO_URI

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient | None:
    """Return a cached MongoClient, or None if MongoDB is unreachable."""
    global _client
    if _client is None:
        candidate = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        try:
            candidate.admin.command("ping")
        except Exception:
            return None
        _client = candidate
    return _client


def get_cache_collection() -> Collection | None:
    """Return the SerpAPI response cache collection, creating its TTL index on first use."""
    client = get_mongo_client()
    if client is None:
        return None

    collection = client[MONGO_DB_NAME]["serpapi_flight_cache"]
    collection.create_index("cached_at", expireAfterSeconds=MONGO_CACHE_TTL_SECONDS)
    return collection


def get_app_collection(name: str) -> Collection | None:
    """Return a collection in the MySQL-mirror database (flight_app), or None if MongoDB is unreachable."""
    client = get_mongo_client()
    if client is None:
        return None
    return client[MONGO_APP_DB_NAME][name]
