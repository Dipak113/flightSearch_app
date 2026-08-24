"""Application configuration, loaded from environment variables (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "flight_db"),
}

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "flight_cache")
MONGO_CACHE_TTL_SECONDS = int(os.getenv("MONGO_CACHE_TTL_SECONDS", str(60 * 60 * 6)))  # 6 hours

# Database mirrored from MySQL on every write (airports/searches/flights collections)
MONGO_APP_DB_NAME = os.getenv("MONGO_APP_DB_NAME", "flight_app")
