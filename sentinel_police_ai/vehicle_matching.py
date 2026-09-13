import sqlite3
import os
import json


# =========================================================
# VEHICLE MATCHING SYSTEM
# =========================================================

DATABASE_PATH = "output/vehicle_database.db"

FINAL_RECORDS = "output/final_vehicle_records.json"


# =========================================================
# LOAD FINAL VEHICLE RECORDS
# =========================================================

def load_vehicle_records():

    if not os.path.exists(FINAL_RECORDS):

        print(
            "ERROR: final_vehicle_records.json not found."
        )

        return []

    try:

        with open(
            FINAL_RECORDS,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"ERROR reading vehicle records: {e}"
        )

        return []


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect():

    if not os.path.exists(DATABASE_PATH):

        print(
            "ERROR: Vehicle database not found."
        )

        return None

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# SEARCH BY VEHICLE ID
# =========================================================

def search_by_vehicle_id(vehicle_id):

    connection = connect()

    if connection is None:
        return None

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM vehicles
        WHERE vehicle_id = ?
        """,
        (vehicle_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result:
        return dict(result)

    return None


# =========================================================
# SEARCH BY NUMBER PLATE
# =========================================================

def search_by_plate(number_plate):

    connection = connect()

    if connection is None:
        return None

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM vehicles
        WHERE number_plate = ?
        """,
        (number_plate.upper(),)
    )

    result = cursor.fetchone()

    connection.close()

    if result:
        return dict(result)

    return None


# =========================================================
# SEARCH BY VEHICLE TYPE
# =========================================================

def search_by_type(vehicle_type):

    connection = connect()

    if connection is None:
        return []

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM vehicles
        WHERE vehicle_type = ?
        """,
        (vehicle_type,)
    )

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return results


# =========================================================
# SEARCH BY COLOR
# =========================================================

def search_by_color(color):

    connection = connect()

    if connection is None:
        return []

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM vehicles
        WHERE color = ?
        """,
        (color,)
    )

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return results


# =========================================================
# GET VEHICLE HISTORY
# =========================================================

def get_vehicle_history(vehicle_id):

    connection = connect()

    if connection is None:
        return []

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM detections
        WHERE vehicle_id = ?
        ORDER BY frame_number
        """,
        (vehicle_id,)
    )

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return results


# =========================================================
# DISPLAY VEHICLE
# =========================================================

def display_vehicle(vehicle):

    if vehicle is None:

        print("\nVehicle not found.")

        return

    print("\n" + "=" * 60)
    print("VEHICLE MATCH FOUND")
    print("=" * 60)

    print(
        f"Vehicle ID          : "
        f"{vehicle.get('vehicle_id')}"
    )

    print(
        f"Tracking ID         : "
        f"{vehicle.get('tracking_id')}"
    )

    print(
        f"Vehicle Type        : "
        f"{vehicle.get('vehicle_type')}"
    )

    print(
        f"Color               : "
        f"{vehicle.get('color')}"
    )

    print(
        f"Number Plate        : "
        f"{vehicle.get('number_plate')}"
    )

    print(
        f"Plate Confidence    : "
        f"{vehicle.get('plate_confidence')}%"
    )

    print(
        f"Detection Confidence: "
        f"{vehicle.get('detection_confidence')}%"
    )

    print(
        f"Last Updated        : "
        f"{vehicle.get('created_at')}"
    )

    print("=" * 60)


# =========================================================
# DISPLAY HISTORY
# =========================================================

def display_history(vehicle_id):

    history = get_vehicle_history(
        vehicle_id
    )

    print("\n" + "=" * 60)
    print("VEHICLE TRACKING HISTORY")
    print("=" * 60)

    if not history:

        print("No tracking history found.")

        return

    print(
        f"Total observations: "
        f"{len(history)}"
    )

    print()

    for record in history:

        print(
            f"Frame {record.get('frame_number')} | "
            f"Track {record.get('tracking_id')} | "
            f"Confidence {record.get('confidence')}%"
        )


# =========================================================
# MAIN SEARCH
# =========================================================

def main():

    print("=" * 60)
    print("       VEHICLE MATCHING SYSTEM")
    print("=" * 60)

    print("\nSearch options:")
    print("1. Vehicle ID")
    print("2. Number Plate")
    print("3. Vehicle Type")
    print("4. Color")
    print("5. Exit")

    choice = input(
        "\nEnter choice: "
    ).strip()

    # -----------------------------------------------------
    # VEHICLE ID
    # -----------------------------------------------------

    if choice == "1":

        vehicle_id = input(
            "Enter vehicle ID: "
        ).strip()

        vehicle = search_by_vehicle_id(
            vehicle_id
        )

        display_vehicle(
            vehicle
        )

        if vehicle:

            display_history(
                vehicle_id
            )

    # -----------------------------------------------------
    # NUMBER PLATE
    # -----------------------------------------------------

    elif choice == "2":

        plate = input(
            "Enter number plate: "
        ).strip()

        vehicle = search_by_plate(
            plate
        )

        display_vehicle(
            vehicle
        )

        if vehicle:

            display_history(
                vehicle["vehicle_id"]
            )

    # -----------------------------------------------------
    # VEHICLE TYPE
    # -----------------------------------------------------

    elif choice == "3":

        vehicle_type = input(
            "Enter vehicle type "
            "(Car/Motorcycle/Bus/Truck): "
        ).strip()

        vehicles = search_by_type(
            vehicle_type
        )

        print(
            f"\nVehicles found: "
            f"{len(vehicles)}"
        )

        for vehicle in vehicles:

            display_vehicle(
                vehicle
            )

    # -----------------------------------------------------
    # COLOR
    # -----------------------------------------------------

    elif choice == "4":

        color = input(
            "Enter color: "
        ).strip()

        vehicles = search_by_color(
            color
        )

        print(
            f"\nVehicles found: "
            f"{len(vehicles)}"
        )

        for vehicle in vehicles:

            display_vehicle(
                vehicle
            )

    # -----------------------------------------------------
    # EXIT
    # -----------------------------------------------------

    elif choice == "5":

        print(
            "\nExiting..."
        )

        return

    else:

        print(
            "\nInvalid choice."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()