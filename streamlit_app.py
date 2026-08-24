"""Streamlit front end for the Flight Search Application."""
import pandas as pd
import streamlit as st

from db.connection import connect_database
from repositories.airports import AirportAlreadyExists, add_airport, get_airports
from repositories.flights import add_flight, get_all_flights, get_flights_by_search
from repositories.searches import InvalidSearch, create_search, delete_search, get_searches
from services.serpapi_flights import SerpApiError, search_flights

st.set_page_config(page_title="Flight Search", page_icon="✈️", layout="wide")


@st.cache_resource
def get_connection():
    return connect_database()


def require_connection():
    connection = get_connection()
    if connection is None or not connection.is_connected():
        get_connection.clear()
        connection = get_connection()
    if connection is None:
        st.error(
            "Could not connect to the database. Check DB_HOST / DB_USER / DB_PASSWORD / "
            "DB_NAME in your .env file and make sure MySQL is running."
        )
        st.stop()
    return connection


connection = require_connection()

st.title("✈️ Flight Search Application")

with st.sidebar:
    st.header("Navigation")
    section = st.radio(
        "Section", ["📍 Airports", "🔍 Searches", "🛫 Flights"], label_visibility="collapsed"
    )

    flights_view = None
    if section == "🛫 Flights":
        st.divider()
        st.subheader("Flights view")
        flights_view = st.radio(
            "Flights view",
            ["🔎 Live Search (SerpAPI)", "➕ Add Manually", "📋 By Search", "📊 All Flights"],
            label_visibility="collapsed",
        )

# ==================== AIRPORTS ====================
if section == "📍 Airports":
    st.subheader("Add Airport")
    with st.form("add_airport_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        iata_code = col1.text_input("IATA Code (e.g., DEL, BOM)")
        airport_name = col2.text_input("Airport Name")
        if st.form_submit_button("Add Airport"):
            if not iata_code or not airport_name:
                st.warning("Enter both an IATA code and an airport name.")
            else:
                try:
                    add_airport(connection, iata_code, airport_name)
                    st.success(f"Airport {iata_code.strip().upper()} added successfully!")
                    st.rerun()
                except AirportAlreadyExists as e:
                    st.error(f"Airport {e} already exists!")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.subheader("All Airports")
    airports = get_airports(connection)
    if airports:
        airports_df = pd.DataFrame(airports, columns=["Airport ID", "IATA Code", "Airport Name"])
        st.dataframe(airports_df, use_container_width=True, hide_index=True)
    else:
        st.info("No airports found. Add one above.")

# ==================== SEARCHES ====================
elif section == "🔍 Searches":
    st.subheader("Create New Search")

    airports = get_airports(connection)
    if len(airports) < 2:
        st.warning("Add at least 2 airports before creating a search.")
    else:
        airport_options = {f"{a[1]} — {a[2]} (ID {a[0]})": a[0] for a in airports}
        with st.form("create_search_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            source_label = col1.selectbox("Source Airport", list(airport_options.keys()))
            destination_label = col2.selectbox("Destination Airport", list(airport_options.keys()))
            travel_date = col3.date_input("Travel Date")
            if st.form_submit_button("Create Search"):
                try:
                    search_id = create_search(
                        connection,
                        airport_options[source_label],
                        airport_options[destination_label],
                        travel_date.strftime("%Y-%m-%d"),
                    )
                    st.success(f"Search created! Search ID: {search_id}")
                    st.rerun()
                except InvalidSearch as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {e}")

    st.subheader("All Searches")
    searches = get_searches(connection)
    if searches:
        searches_df = pd.DataFrame(
            searches, columns=["Search ID", "From", "To", "Travel Date", "Search Time"]
        )
        st.dataframe(searches_df, use_container_width=True, hide_index=True)

        st.subheader("Delete a Search")
        col1, col2 = st.columns([3, 1])
        delete_id = col1.selectbox("Search ID to delete", [s[0] for s in searches], key="delete_search_id")
        col2.write("")
        if col2.button("Delete Search (and its flights)", type="primary"):
            if delete_search(connection, delete_id):
                st.success(f"Search {delete_id} deleted successfully!")
                st.rerun()
            else:
                st.error(f"Search {delete_id} not found!")
    else:
        st.info("No searches found. Create one above.")

# ==================== FLIGHTS ====================
elif section == "🛫 Flights":
    searches = get_searches(connection)
    search_options = {f"#{s[0]}: {s[1]} → {s[2]} on {s[3]}": s[0] for s in searches}

    if not searches:
        st.info("Create a search first, on the Searches tab.")

    elif flights_view == "🔎 Live Search (SerpAPI)":
        st.subheader("🔎 Live Flight Search (SerpAPI)")

        live_label = st.selectbox("Search", list(search_options.keys()), key="live_search_select")
        live_search_id = search_options[live_label]
        chosen_search = next(s for s in searches if s[0] == live_search_id)
        source_iata, destination_iata, travel_date = chosen_search[1], chosen_search[2], str(chosen_search[3])

        col1, col2 = st.columns([1, 2])
        use_cache = col1.checkbox("Use cached results", value=True, help="Served from MongoDB if we've searched this route+date recently")
        if col2.button("Search Live Flights"):
            try:
                with st.spinner(f"Searching {source_iata} → {destination_iata} on {travel_date}..."):
                    results, from_cache = search_flights(source_iata, destination_iata, travel_date, use_cache=use_cache)
                st.session_state["live_flight_results"] = results
                st.session_state["live_flight_search_id"] = live_search_id
                st.session_state["live_flight_from_cache"] = from_cache
            except SerpApiError as e:
                st.error(str(e))
                st.session_state.pop("live_flight_results", None)

        live_results = st.session_state.get("live_flight_results")
        if live_results and st.session_state.get("live_flight_search_id") == live_search_id:
            st.caption("♻️ Served from MongoDB cache" if st.session_state["live_flight_from_cache"] else "🌐 Fresh result from SerpAPI (now cached)")

            if not live_results:
                st.info("No flights found for this route and date.")
            else:
                live_df = pd.DataFrame(live_results)
                st.dataframe(live_df, use_container_width=True, hide_index=True)

                option_labels = [
                    f"{r['airline']} — ₹{r['price']} — {r['departure_time']} → {r['arrival_time']} ({r['stops']} stop(s))"
                    for r in live_results
                ]
                chosen_label = st.selectbox("Pick a flight to save into this search", option_labels, key="live_flight_choice")
                if st.button("Save Selected Flight"):
                    chosen = live_results[option_labels.index(chosen_label)]
                    try:
                        add_flight(
                            connection,
                            live_search_id,
                            chosen["airline"],
                            chosen["departure_airport"] or source_iata,
                            chosen["arrival_airport"] or destination_iata,
                            chosen["departure_time"],
                            chosen["arrival_time"],
                            int(chosen["duration_minutes"] or 0),
                            float(chosen["price"] or 0),
                        )
                        st.success("Flight saved to this search!")
                        st.session_state.pop("live_flight_results", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    elif flights_view == "➕ Add Manually":
        st.subheader("Add Flight to a Search (manual)")
        with st.form("add_flight_form", clear_on_submit=True):
            search_label = st.selectbox("Search", list(search_options.keys()))
            col1, col2 = st.columns(2)
            airline = col1.text_input("Airline Name")
            price = col2.number_input("Price (₹)", min_value=0.0, step=100.0)

            col3, col4 = st.columns(2)
            departure_airport = col3.text_input("Departure Airport (IATA)")
            arrival_airport = col4.text_input("Arrival Airport (IATA)")

            col5, col6 = st.columns(2)
            departure_dt = col5.text_input("Departure Time (YYYY-MM-DD HH:MM:SS)")
            arrival_dt = col6.text_input("Arrival Time (YYYY-MM-DD HH:MM:SS)")

            duration_minutes = st.number_input("Duration (minutes)", min_value=0, step=5)

            if st.form_submit_button("Add Flight"):
                if not all([airline, departure_airport, arrival_airport, departure_dt, arrival_dt]):
                    st.warning("Fill in all flight details.")
                else:
                    try:
                        add_flight(
                            connection,
                            search_options[search_label],
                            airline,
                            departure_airport,
                            arrival_airport,
                            departure_dt,
                            arrival_dt,
                            int(duration_minutes),
                            float(price),
                        )
                        st.success("Flight added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    elif flights_view == "📋 By Search":
        st.subheader("Flights by Search")
        view_label = st.selectbox("Search", list(search_options.keys()), key="view_flights_search")
        flights = get_flights_by_search(connection, search_options[view_label])
        if flights:
            flights_df = pd.DataFrame(
                flights,
                columns=[
                    "Flight ID", "Airline", "From", "To",
                    "Departure", "Arrival", "Duration (min)", "Price (₹)",
                ],
            )
            st.dataframe(flights_df, use_container_width=True, hide_index=True)
        else:
            st.info("No flights found for this search.")

    elif flights_view == "📊 All Flights":
        st.subheader("All Flights")
        all_flights = get_all_flights(connection)
        if all_flights:
            all_flights_df = pd.DataFrame(
                all_flights,
                columns=[
                    "Flight ID", "Airline", "From", "To", "Departure",
                    "Arrival", "Duration (min)", "Price (₹)", "Search ID",
                ],
            )
            st.dataframe(all_flights_df, use_container_width=True, hide_index=True)
        else:
            st.info("No flights found.")
