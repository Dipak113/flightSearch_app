"""Console menu for the Flight Search Application."""
from db.connection import connect_database
from repositories.airports import AirportAlreadyExists, add_airport, get_airports
from repositories.flights import add_flight, get_all_flights, get_flights_by_search
from repositories.searches import InvalidSearch, create_search, delete_search, get_searches
from services.serpapi_flights import SerpApiError, search_flights


# ==================== ADD AIRPORT ====================
def prompt_add_airport(connection) -> None:
    iata_code = input("Enter Airport IATA Code (e.g., DEL, BOM): ")
    airport_name = input("Enter Airport Name: ")

    try:
        add_airport(connection, iata_code, airport_name)
        print(f"\n✅ Airport {iata_code.strip().upper()} added successfully!\n")
    except AirportAlreadyExists as e:
        print(f"\n❌ Airport {e} already exists!\n")
    except Exception as e:
        print(f"❌ Error: {e}")


# ==================== VIEW ALL AIRPORTS ====================
def prompt_view_airports(connection) -> list[tuple]:
    try:
        airports = get_airports(connection)

        if len(airports) == 0:
            print("\n❌ No airports found. Please add airports first.\n")
        else:
            print("\n" + "=" * 40)
            print("AVAILABLE AIRPORTS")
            print("=" * 40)
            print(f"{'ID':<10} {'IATA Code':<15}")
            print("-" * 40)

            for airport in airports:
                print(f"{airport[0]:<10} {airport[1]:<15}")

            print("=" * 40 + "\n")

        return airports

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


# ==================== CREATE SEARCH ====================
def prompt_create_search(connection) -> int | None:
    try:
        airports = prompt_view_airports(connection)

        if len(airports) < 2:
            print("❌ Need at least 2 airports to search flights.\n")
            return None

        source_id = int(input("Enter Source Airport ID: "))
        destination_id = int(input("Enter Destination Airport ID: "))
        travel_date = input("Enter Travel Date (YYYY-MM-DD): ").strip()

        search_id = create_search(connection, source_id, destination_id, travel_date)
        print(f"\n✅ Search created successfully! Search ID: {search_id}\n")
        return search_id

    except InvalidSearch as e:
        print(f"\n❌ {e}\n")
        return None
    except ValueError:
        print("\n❌ Please enter valid numbers!\n")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ==================== VIEW ALL SEARCHES ====================
def prompt_view_searches(connection) -> list[tuple]:
    try:
        searches = get_searches(connection)

        if len(searches) == 0:
            print("\n❌ No searches found.\n")
        else:
            print("\n" + "=" * 80)
            print("ALL SEARCHES")
            print("=" * 80)
            print(f"{'ID':<8} {'From':<10} {'To':<10} {'Date':<15} {'Search Time':<20}")
            print("-" * 80)

            for search in searches:
                print(f"{search[0]:<8} {search[1]:<10} {search[2]:<10} {search[3]:<15} {search[4]}")

            print("=" * 80 + "\n")

        return searches

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


# ==================== ADD FLIGHT ====================
def prompt_add_flight(connection) -> None:
    try:
        searches = prompt_view_searches(connection)

        if len(searches) == 0:
            print("❌ Create a search first!\n")
            return

        search_id = int(input("Enter Search ID to add flight: "))

        print("\n--- Enter Flight Details ---")
        airline = input("Airline Name: ")
        departure_airport = input("Departure Airport (IATA): ")
        arrival_airport = input("Arrival Airport (IATA): ")
        departure_time = input("Departure Time (YYYY-MM-DD HH:MM:SS): ").strip()
        arrival_time = input("Arrival Time (YYYY-MM-DD HH:MM:SS): ").strip()
        duration_minutes = int(input("Duration (minutes): "))
        price = float(input("Price: "))

        add_flight(
            connection, search_id, airline, departure_airport, arrival_airport,
            departure_time, arrival_time, duration_minutes, price,
        )
        print("\n✅ Flight added successfully!\n")

    except ValueError:
        print("\n❌ Please enter valid numbers!\n")
    except Exception as e:
        print(f"❌ Error: {e}")


# ==================== LIVE FLIGHT SEARCH (SERPAPI) ====================
def prompt_live_flight_search(connection) -> None:
    try:
        searches = prompt_view_searches(connection)

        if len(searches) == 0:
            print("❌ Create a search first!\n")
            return

        search_id = int(input("Enter Search ID to look up live flights for: "))
        search = next((s for s in searches if s[0] == search_id), None)

        if search is None:
            print(f"\n❌ Search {search_id} not found!\n")
            return

        _, source_iata, destination_iata, travel_date, _ = search
        use_cache = input("Use cached results if available? (yes/no) [yes]: ").strip().lower() != "no"

        print(f"\nSearching {source_iata} → {destination_iata} on {travel_date}...\n")
        results, from_cache = search_flights(source_iata, destination_iata, str(travel_date), use_cache=use_cache)

        print("♻️  Served from MongoDB cache\n" if from_cache else "🌐 Fresh result from SerpAPI (now cached)\n")

        if len(results) == 0:
            print("❌ No flights found for this route and date.\n")
            return

        print("=" * 100)
        print(f"{'#':<4} {'Airline':<20} {'Departure':<20} {'Arrival':<20} {'Dur(min)':<10} {'Stops':<7} {'Price':<10}")
        print("-" * 100)
        for i, r in enumerate(results, start=1):
            print(
                f"{i:<4} {r['airline']:<20} {r['departure_time']:<20} {r['arrival_time']:<20} "
                f"{r['duration_minutes']:<10} {r['stops']:<7} ₹{r['price']:<10}"
            )
        print("=" * 100 + "\n")

        choice = input("Enter # to save into this search (or blank to skip): ").strip()
        if not choice:
            return

        chosen = results[int(choice) - 1]
        add_flight(
            connection,
            search_id,
            chosen["airline"],
            chosen["departure_airport"] or source_iata,
            chosen["arrival_airport"] or destination_iata,
            chosen["departure_time"],
            chosen["arrival_time"],
            int(chosen["duration_minutes"] or 0),
            float(chosen["price"] or 0),
        )
        print("\n✅ Flight saved to search!\n")

    except SerpApiError as e:
        print(f"\n❌ {e}\n")
    except (ValueError, IndexError):
        print("\n❌ Please enter a valid number from the list!\n")
    except Exception as e:
        print(f"❌ Error: {e}")


# ==================== VIEW FLIGHTS BY SEARCH ====================
def prompt_view_flights_by_search(connection) -> None:
    try:
        searches = prompt_view_searches(connection)

        if len(searches) == 0:
            return

        search_id = int(input("Enter Search ID to view flights: "))
        flights = get_flights_by_search(connection, search_id)

        if len(flights) == 0:
            print(f"\n❌ No flights found for Search ID {search_id}\n")
        else:
            print("\n" + "=" * 100)
            print(f"FLIGHTS FOR SEARCH ID: {search_id}")
            print("=" * 100)
            print(
                f"{'ID':<6} {'Airline':<20} {'From':<8} {'To':<8} {'Departure':<20} "
                f"{'Arrival':<20} {'Dur(min)':<10} {'Price':<10}"
            )
            print("-" * 100)

            for flight in flights:
                print(
                    f"{flight[0]:<6} {flight[1]:<20} {flight[2]:<8} {flight[3]:<8} "
                    f"{str(flight[4]):<20} {str(flight[5]):<20} {flight[6]:<10} ₹{flight[7]:<10}"
                )

            print("=" * 100 + "\n")

    except ValueError:
        print("\n❌ Please enter a valid number!\n")
    except Exception as e:
        print(f"❌ Error: {e}")


# ==================== VIEW ALL FLIGHTS ====================
def prompt_view_all_flights(connection) -> None:
    try:
        flights = get_all_flights(connection)

        if len(flights) == 0:
            print("\n❌ No flights found.\n")
        else:
            print("\n" + "=" * 110)
            print("ALL FLIGHTS")
            print("=" * 110)
            print(
                f"{'ID':<6} {'SrchID':<8} {'Airline':<20} {'From':<8} {'To':<8} "
                f"{'Departure':<20} {'Arrival':<20} {'Dur':<8} {'Price':<10}"
            )
            print("-" * 110)

            for flight in flights:
                print(
                    f"{flight[0]:<6} {flight[8]:<8} {flight[1]:<20} {flight[2]:<8} {flight[3]:<8} "
                    f"{str(flight[4]):<20} {str(flight[5]):<20} {flight[6]:<8} ₹{flight[7]:<10}"
                )

            print("=" * 110 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")


# ==================== DELETE SEARCH ====================
def prompt_delete_search(connection) -> None:
    try:
        searches = prompt_view_searches(connection)

        if len(searches) == 0:
            return

        search_id = int(input("Enter Search ID to delete: "))
        confirm = input(f"\n⚠️  Delete search {search_id} and all flights? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("Operation cancelled.\n")
            return

        if delete_search(connection, search_id):
            print(f"\n✅ Search {search_id} deleted successfully!\n")
        else:
            print(f"\n❌ Search {search_id} not found!\n")

    except ValueError:
        print("\n❌ Please enter a valid number!\n")
    except Exception as e:
        print(f"❌ Error: {e}")


# ==================== MAIN MENU ====================
def main_menu() -> None:
    connection = connect_database()

    if connection is None:
        print("❌ Error: could not connect to the database.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure MySQL is running")
        print("2. Check DB_USER / DB_PASSWORD in your .env file")
        print("3. Make sure the 'flight_db' database exists\n")
        return

    print("✅ Database connected successfully!\n")

    while True:
        print("\n" + "=" * 50)
        print("       ✈️  FLIGHT SEARCH APPLICATION")
        print("=" * 50)
        print("\n📍 AIRPORT MANAGEMENT")
        print("1. Add Airport")
        print("2. View All Airports")
        print("\n🔍 SEARCH MANAGEMENT")
        print("3. Create New Search")
        print("4. View All Searches")
        print("5. Delete Search")
        print("\n✈️  FLIGHT MANAGEMENT")
        print("6. Add Flight to Search (manual)")
        print("7. View Flights by Search ID")
        print("8. View All Flights")
        print("9. Live Flight Search (SerpAPI)")
        print("\n10. Exit")
        print("=" * 50)

        choice = input("\nEnter your choice (1-10): ").strip()

        if choice == "1":
            prompt_add_airport(connection)
        elif choice == "2":
            prompt_view_airports(connection)
        elif choice == "3":
            prompt_create_search(connection)
        elif choice == "4":
            prompt_view_searches(connection)
        elif choice == "5":
            prompt_delete_search(connection)
        elif choice == "6":
            prompt_add_flight(connection)
        elif choice == "7":
            prompt_view_flights_by_search(connection)
        elif choice == "8":
            prompt_view_all_flights(connection)
        elif choice == "9":
            prompt_live_flight_search(connection)
        elif choice == "10":
            print("\n✈️  Thank you for using Flight Search Application!")
            print("Goodbye! 👋\n")
            break
        else:
            print("\n❌ Invalid choice! Please enter 1-10.\n")

    connection.close()
    print("Database connection closed.")
