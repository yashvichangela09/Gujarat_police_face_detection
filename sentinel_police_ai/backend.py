import json
import sqlite3
import os


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

DATABASE_PATH = os.path.join(
    OUTPUT_DIR,
    "vehicle_database.db"
)

VEHICLE_DATA = os.path.join(
    OUTPUT_DIR,
    "final_vehicle_records.json"
)

TRACKING_DATA = os.path.join(
    OUTPUT_DIR,
    "tracking_records.json"
)


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path, default=None):

    if default is None:
        default = []

    if not os.path.exists(path):
        return default

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(f"Error loading {path}: {e}")

        return default


# =========================================================
# GET VEHICLE RECORDS
# =========================================================

def get_vehicles():

    return load_json(
        VEHICLE_DATA,
        []
    )


# =========================================================
# GET TRACKING RECORDS
# =========================================================

def get_tracking_records():

    return load_json(
        TRACKING_DATA,
        []
    )


# =========================================================
# GET VEHICLE BY ID
# =========================================================

def get_vehicle_by_id(vehicle_id):

    vehicles = get_vehicles()

    for vehicle in vehicles:

        if vehicle.get("vehicle_id") == vehicle_id:
            return vehicle

    return None


# =========================================================
# SEARCH BY NUMBER PLATE
# =========================================================

def search_by_plate(number_plate):

    vehicles = get_vehicles()

    number_plate = number_plate.upper().strip()

    results = []

    for vehicle in vehicles:

        plate = str(
            vehicle.get(
                "number_plate",
                ""
            )
        ).upper()

        if number_plate in plate:

            results.append(vehicle)

    return results


# =========================================================
# GET DASHBOARD STATISTICS
# =========================================================

def get_statistics():

    vehicles = get_vehicles()

    tracking = get_tracking_records()


    total_vehicles = len(vehicles)

    total_detections = len(tracking)


    vehicle_types = {}

    colors = {}


    for vehicle in vehicles:

        vehicle_type = vehicle.get(
            "vehicle_type",
            "Unknown"
        )

        color = vehicle.get(
            "color",
            "Unknown"
        )


        vehicle_types[vehicle_type] = (
            vehicle_types.get(
                vehicle_type,
                0
            ) + 1
        )


        colors[color] = (
            colors.get(
                color,
                0
            ) + 1
        )


    return {

        "total_vehicles":
            total_vehicles,

        "total_detections":
            total_detections,

        "vehicle_types":
            vehicle_types,

        "colors":
            colors
    }


# =========================================================
# GET RECENT VEHICLES
# =========================================================

def get_recent_vehicles(limit=10):

    vehicles = get_vehicles()

    return vehicles[-limit:]


# =========================================================
# DATABASE CHECK
# =========================================================

def database_status():

    if not os.path.exists(DATABASE_PATH):

        return {
            "connected": False,
            "vehicles": 0,
            "detections": 0
        }


    try:

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()


        cursor.execute(
            "SELECT COUNT(*) FROM vehicles"
        )

        vehicle_count = cursor.fetchone()[0]


        cursor.execute(
            "SELECT COUNT(*) FROM detections"
        )

        detection_count = cursor.fetchone()[0]


        connection.close()


        return {

            "connected": True,

            "vehicles":
                vehicle_count,

            "detections":
                detection_count
        }


    except Exception:

        return {

            "connected": False,

            "vehicles": 0,

            "detections": 0
        }


# =========================================================
# COMPLETE BACKEND DATA
# =========================================================

def get_dashboard_data():

    statistics = get_statistics()

    return {

        "statistics":
            statistics,

        "vehicles":
            get_vehicles(),

        "recent_vehicles":
            get_recent_vehicles(),

        "database":
            database_status()
    }


# =========================================================
# TEST BACKEND
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("          VEHICLE RECOGNITION BACKEND")
    print("=" * 60)


    data = get_dashboard_data()


    print("\nDashboard Statistics")
    print("-" * 40)

    print(
        "Total vehicles:",
        data["statistics"]["total_vehicles"]
    )

    print(
        "Total detections:",
        data["statistics"]["total_detections"]
    )


    print("\nVehicle Types")
    print("-" * 40)

    for vehicle_type, count in (
        data["statistics"]["vehicle_types"].items()
    ):

        print(
            f"{vehicle_type}: {count}"
        )


    print("\nColors")
    print("-" * 40)

    for color, count in (
        data["statistics"]["colors"].items()
    ):

        print(
            f"{color}: {count}"
        )


    print("\nDatabase")
    print("-" * 40)

    print(
        "Connected:",
        data["database"]["connected"]
    )

    print(
        "Vehicles:",
        data["database"]["vehicles"]
    )

    print(
        "Detections:",
        data["database"]["detections"]
    )


    print("\nBackend ready.")
    print("=" * 60)