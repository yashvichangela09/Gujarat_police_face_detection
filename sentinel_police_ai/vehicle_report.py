import sqlite3
import csv
import os
import json


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_PATH = os.path.join(
    "output",
    "vehicle_database.db"
)

OUTPUT_DIR = "output"

JSON_REPORT = os.path.join(
    OUTPUT_DIR,
    "vehicle_report.json"
)

CSV_REPORT = os.path.join(
    OUTPUT_DIR,
    "vehicle_report.csv"
)


# =========================================================
# LOAD VEHICLES
# =========================================================

def get_vehicles():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            vehicle_id,
            tracking_id,
            vehicle_type,
            color,
            number_plate,
            plate_confidence,
            detection_confidence,
            appearance,
            created_at
        FROM vehicles
        ORDER BY id
    """)

    vehicles = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return vehicles


# =========================================================
# SAVE JSON REPORT
# =========================================================

def save_json_report(vehicles):

    with open(
        JSON_REPORT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            vehicles,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# SAVE CSV REPORT
# =========================================================

def save_csv_report(vehicles):

    if not vehicles:
        return

    fieldnames = [
        "vehicle_id",
        "tracking_id",
        "vehicle_type",
        "color",
        "number_plate",
        "plate_confidence",
        "detection_confidence",
        "appearance",
        "created_at"
    ]

    with open(
        CSV_REPORT,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for vehicle in vehicles:

            writer.writerow(vehicle)


# =========================================================
# DISPLAY SUMMARY
# =========================================================

def display_summary(vehicles):

    print()
    print("=" * 60)
    print("             VEHICLE REPORT")
    print("=" * 60)

    print(
        f"Total vehicles: {len(vehicles)}"
    )

    print()

    # -----------------------------------------------------
    # Vehicle type count
    # -----------------------------------------------------

    type_counts = {}

    for vehicle in vehicles:

        vehicle_type = vehicle.get(
            "vehicle_type",
            "Unknown"
        )

        type_counts[vehicle_type] = (
            type_counts.get(vehicle_type, 0) + 1
        )

    print("VEHICLE TYPES")
    print("-" * 40)

    for vehicle_type, count in type_counts.items():

        print(
            f"{vehicle_type}: {count}"
        )

    print()

    # -----------------------------------------------------
    # Color count
    # -----------------------------------------------------

    color_counts = {}

    for vehicle in vehicles:

        color = vehicle.get(
            "color",
            "Unknown"
        )

        color_counts[color] = (
            color_counts.get(color, 0) + 1
        )

    print("VEHICLE COLORS")
    print("-" * 40)

    for color, count in color_counts.items():

        print(
            f"{color}: {count}"
        )

    print()

    # -----------------------------------------------------
    # Vehicle details
    # -----------------------------------------------------

    print("VEHICLE DETAILS")
    print("-" * 60)

    for vehicle in vehicles:

        print(
            f"{vehicle.get('vehicle_id', 'Unknown')} | "
            f"{vehicle.get('vehicle_type', 'Unknown')} | "
            f"{vehicle.get('color', 'Unknown')} | "
            f"Plate: "
            f"{vehicle.get('number_plate', 'UNKNOWN')}"
        )

    print("=" * 60)


# =========================================================
# MAIN
# =========================================================

def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    if not os.path.exists(
        DATABASE_PATH
    ):

        print(
            "ERROR: Database not found."
        )

        print(
            "Run vehicle_pipeline.py first."
        )

        return


    print(
        "Generating vehicle report..."
    )


    vehicles = get_vehicles()


    if not vehicles:

        print(
            "No vehicles found in database."
        )

        return


    # -----------------------------------------------------
    # Generate reports
    # -----------------------------------------------------

    save_json_report(
        vehicles
    )

    save_csv_report(
        vehicles
    )


    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    display_summary(
        vehicles
    )


    print()
    print("Reports generated:")
    print(JSON_REPORT)
    print(CSV_REPORT)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()