# ✈️ Flight Search App

A flight search application built with **Python** and **Streamlit**. It pulls live flight results from Google Flights through **SerpAPI**, stores airports, searches and flights in **MySQL**, and uses **MongoDB** to cache API responses and keep a copy of the app data.

🌐 **Live demo (Azure):** https://flightsearchapp-gfb4ece9aggpajgp.centralindia-01.azurewebsites.net/

---

## Features

- **Airports**: add airports (IATA code, name, city) and see them all in one list
- **Searches**: create a search from a source airport to a destination airport for a travel date, and view or delete saved searches
- **Live flight search**: fetch real flight options (airline, times, duration, stops, price) from SerpAPI's Google Flights engine and save the ones you want to a search
- **MongoDB caching**: SerpAPI responses are cached for 6 hours by default, so a repeated search for the same route and date doesn't spend another API credit
- **MongoDB copy of app data**: every MySQL write is also saved to a MongoDB `flight_app` database
- **Manual flights**: add a flight to a search by hand
- **Two front ends**: a Streamlit web UI and an interactive console (CLI) version

## Tech Stack

| Layer            | Technology                          |
| ---------------- | ----------------------------------- |
| UI               | Streamlit, pandas                   |
| Live flight data | SerpAPI (Google Flights engine)     |
| Main database    | MySQL                               |
| Cache and copy   | MongoDB (Atlas)                     |
| Hosting          | Azure App Service (Linux)           |

## Project Structure

```
flightSearch_app/
├── streamlit_app.py         # Streamlit web UI
├── main.py                  # Console (CLI) entry point
├── config.py                # Settings loaded from environment variables / .env
├── cli/main.py              # Console menus
├── db/
│   ├── connection.py        # MySQL connection helpers
│   └── mongo.py             # MongoDB client, cache and copy collections
├── repositories/            # Airports, searches and flights data access
├── services/
│   └── serpapi_flights.py   # SerpAPI client with MongoDB caching
├── requirements.txt
└── .env.example             # Template for environment variables
```

## Running Locally

### 1. Prerequisites

- Python 3.10+
- A running MySQL server with a `flight_db` database containing the `airports`, `searches` and `flights` tables
- A MongoDB instance (local or [MongoDB Atlas](https://www.mongodb.com/atlas)). The app still runs without it, but caching is turned off.
- A [SerpAPI](https://serpapi.com/) API key

### 2. Install

```bash
git clone https://github.com/Dipak113/flightSearch_app.git
cd flightSearch_app
pip install -r requirements.txt
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your values:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=flight_db

SERPAPI_KEY=your_serpapi_key
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
MONGO_DB_NAME=flight_cache
MONGO_CACHE_TTL_SECONDS=21600
MONGO_APP_DB_NAME=flight_app
```

> `.env` is in `.gitignore`. Never commit your real credentials.

### 4. Run

Web UI:

```bash
streamlit run streamlit_app.py
```

Console version:

```bash
python main.py
```

## ☁️ Deployment on Azure

The app is deployed to **Azure App Service** and connects to:

- **Azure Database for MySQL (Flexible Server)** for airports, searches and flights
- **MongoDB Atlas** for the SerpAPI response cache and the copy of app data
- **SerpAPI** for live Google Flights results

`config.py` reads every setting from environment variables, so no code changes are needed on Azure. Set the same keys as in `.env` (`DB_*`, `SERPAPI_KEY`, `MONGO_*`) under **App Service → Settings → Environment variables**.

Use this startup command so Streamlit listens on the port App Service expects:

```bash
python -m streamlit run streamlit_app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true
```

In **MongoDB Atlas → Network Access**, allow the App Service's outbound IP addresses so the app can reach the cluster.

🔗 **Live app:** https://flightsearchapp-gfb4ece9aggpajgp.centralindia-01.azurewebsites.net/

## Author

**Dipak**: [GitHub @Dipak113](https://github.com/Dipak113)
