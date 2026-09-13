import sqlite3
import os


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_PATH = os.path.join(
    "output",
    "vehicle_database.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# SEARCH BY NUMBER PLATE
# =========================================================

def search_by_plate(number_plate):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        WHERE number_plate = ?
    """, (
        number_plate.upper(),
    ))

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return results


# =========================================================
# SEARCH BY VEHICLE TYPE
# =========================================================

def search_by_type(vehicle_type):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        WHERE vehicle_type = ?
    """, (
        vehicle_type,
    ))

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
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        WHERE color = ?
    """, (
        color,
    ))

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return results


# =========================================================
# SEARCH BY TRACKING ID
# =========================================================

def search_by_tracking_id(tracking_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        WHERE tracking_id = ?
    """, (
        tracking_id,
    ))

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return results


# =========================================================
# GET ALL VEHICLES
# =========================================================

def get_all_vehicles():

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        ORDER BY id
    """)

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

    print("-" * 60)

    print(
        f"Vehicle ID          : "
        f"{vehicle.get('vehicle_id', 'Unknown')}"
    )

    print(
        f"Tracking ID         : "
        f"{vehicle.get('tracking_id', 'Unknown')}"
    )

    print(
        f"Vehicle Type        : "
        f"{vehicle.get('vehicle_type', 'Unknown')}"
    )

    print(
        f"Color               : "
        f"{vehicle.get('color', 'Unknown')}"
    )

    print(
        f"Number Plate        : "
        f"{vehicle.get('number_plate', 'UNKNOWN')}"
    )

    print(
        f"Plate Confidence    : "
        f"{vehicle.get('plate_confidence', 0)}%"
    )

    print(
        f"Detection Confidence: "
        f"{vehicle.get('detection_confidence', 0)}%"
    )

    print(
        f"Created At          : "
        f"{vehicle.get('created_at', 'Unknown')}"
    )

    print("-" * 60)


# =========================================================
# MAIN SEARCH MENU
# =========================================================

def main():

    if not os.path.exists(DATABASE_PATH):

        print(
            "Database does not exist yet."
        )

        print(
            "Run vehicle_pipeline.py first."
        )

        return


    print("=" * 60)
    print("             VEHICLE SEARCH SYSTEM")
    print("=" * 60)

    print("""
1. Search by number plate
2. Search by vehicle type
3. Search by color
4. Search by tracking ID
5. Show all vehicles
6. Exit
""")


    choice = input(
        "Enter your choice: "
    ).strip()


    # =====================================================
    # NUMBER PLATE
    # =====================================================

    if choice == "1":

        plate = input(
            "Enter number plate: "
        ).strip().upper()

        results = search_by_plate(
            plate
        )


    # =====================================================
    # VEHICLE TYPE
    # =====================================================

    elif choice == "2":

        vehicle_type = input(
            "Enter vehicle type: "
        ).strip()

        results = search_by_type(
            vehicle_type
        )


    # =====================================================
    # COLOR
    # =====================================================

    elif choice == "3":

        color = input(
            "Enter color: "
        ).strip()

        results = search_by_color(
            color
        )


    # =====================================================
    # TRACKING ID
    # =====================================================

    elif choice == "4":

        try:

            tracking_id = int(
                input(
                    "Enter tracking ID: "
                )
            )

        except ValueError:

            print(
                "Tracking ID must be a number."
            )

            return

        results = search_by_tracking_id(
            tracking_id
        )


    # =====================================================
    # ALL VEHICLES
    # =====================================================

    elif choice == "5":

        results = get_all_vehicles()


    # =====================================================
    # EXIT
    # =====================================================

    elif choice == "6":

        print(
            "Exiting..."
        )

        return


    else:

        print(
            "Invalid choice."
        )

        return


    # =====================================================
    # DISPLAY RESULTS
    # =====================================================

    print()

    if not results:

        print(
            "No matching vehicles found."
        )

        return


    print(
        f"Vehicles found: {len(results)}"
    )

    for vehicle in results:

        display_vehicle(
            vehicle
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()