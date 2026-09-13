import sqlite3
import os
import json
import time
import threading


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "output")

DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "vehicle_database.db"
)

# WAL mode + busy timeout allow 20–30 camera threads to write
# concurrently without "database is locked" storms.
_BUSY_TIMEOUT_MS = 5000
_db_lock = threading.RLock()

IDENTITY_JSON = os.path.join(
    DATABASE_DIR,
    "final_vehicle_records.json"
)

TRACKING_JSON = os.path.join(
    DATABASE_DIR,
    "tracking_records.json"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect():

    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=_BUSY_TIMEOUT_MS / 1000.0,
        check_same_thread=False,     # camera threads share the DB file
    )

    connection.row_factory = sqlite3.Row

    # WAL: readers never block writers, writers never block readers
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=%d" % _BUSY_TIMEOUT_MS)
    except Exception:
        pass

    return connection


# =========================================================
# CREATE TABLES
# =========================================================

def create_tables():

    connection = connect()

    cursor = connection.cursor()

    # -----------------------------------------------------
    # VEHICLES TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            vehicle_id TEXT UNIQUE,

            tracking_id TEXT,

            vehicle_type TEXT,

            color TEXT,

            number_plate TEXT,

            plate_confidence REAL,

            detection_confidence REAL,

            appearance TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # DETECTIONS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            vehicle_id TEXT,

            frame_number INTEGER,

            tracking_id TEXT,

            camera_id TEXT,

            x1 INTEGER,

            y1 INTEGER,

            x2 INTEGER,

            y2 INTEGER,

            confidence REAL,

            FOREIGN KEY(vehicle_id)
                REFERENCES vehicles(vehicle_id)
        )
    """)

    # migrate older databases that lack the camera_id column
    cols = [row[1] for row in cursor.execute("PRAGMA table_info(detections)")]
    if "camera_id" not in cols:
        cursor.execute(
            "ALTER TABLE detections ADD COLUMN camera_id TEXT"
        )

    connection.commit()

    connection.close()


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path, default):

    if not os.path.exists(path):

        print(
            f"WARNING: File not found: {path}"
        )

        return default

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"ERROR reading {path}: {e}"
        )

        return default


# =========================================================
# INSERT VEHICLE
# =========================================================

def insert_vehicle(vehicle):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO vehicles (

            vehicle_id,

            tracking_id,

            vehicle_type,

            color,

            number_plate,

            plate_confidence,

            detection_confidence,

            appearance

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        vehicle.get(
            "vehicle_id"
        ),

        str(
            vehicle.get(
                "tracking_id"
            )
        ) if vehicle.get(
            "tracking_id"
        ) is not None else None,

        vehicle.get(
            "vehicle_type",
            "Unknown"
        ),

        vehicle.get(
            "color",
            "Unknown"
        ),

        vehicle.get(
            "number_plate",
            "UNKNOWN"
        ),

        vehicle.get(
            "plate_confidence",
            0
        ),

        vehicle.get(
            "detection_confidence",
            0
        ),

        json.dumps(
            vehicle.get(
                "appearance",
                {}
            )
        )
    ))

    connection.commit()

    connection.close()


# =========================================================
# INSERT DETECTION
# =========================================================

def insert_detection(

    vehicle_id,

    frame_number,

    tracking_id,

    bounding_box,

    confidence,

    camera_id=None

):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO detections (

            vehicle_id,

            frame_number,

            tracking_id,

            camera_id,

            x1,

            y1,

            x2,

            y2,

            confidence

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        vehicle_id,

        frame_number,

        str(tracking_id)
        if tracking_id is not None
        else None,

        str(camera_id)
        if camera_id is not None
        else None,

        bounding_box.get(
            "x1",
            0
        ),

        bounding_box.get(
            "y1",
            0
        ),

        bounding_box.get(
            "x2",
            0
        ),

        bounding_box.get(
            "y2",
            0
        ),

        confidence
    ))

    connection.commit()

    connection.close()


# =========================================================
# IMPORT VEHICLE IDENTITIES
# =========================================================

def import_vehicle_identities():

    vehicles = load_json(
        IDENTITY_JSON,
        []
    )

    if not vehicles:

        print(
            "\nNo vehicle identity records found."
        )

        return 0

    count = 0

    for vehicle in vehicles:

        vehicle_id = vehicle.get(
            "vehicle_id"
        )

        if not vehicle_id:
            continue

        insert_vehicle(
            vehicle
        )

        count += 1

    return count


# =========================================================
# IMPORT TRACKING DETECTIONS
# =========================================================

def import_tracking_records():

    tracking_records = load_json(
        TRACKING_JSON,
        []
    )

    if not tracking_records:

        print(
            "\nNo tracking records found."
        )

        return 0

    count = 0

    for record in tracking_records:

        vehicle_id = record.get(
            "vehicle_id"
        )

        if not vehicle_id:
            continue

        bounding_box = record.get(
            "bounding_box",
            {}
        )

        insert_detection(

            vehicle_id=vehicle_id,

            frame_number=record.get(
                "frame",
                0
            ),

            tracking_id=record.get(
                "tracking_id",
                vehicle_id
            ),

            bounding_box=bounding_box,

            confidence=record.get(
                "confidence",
                0
            )
        )

        count += 1

    return count


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

    vehicles = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return vehicles


# =========================================================
# SEARCH VEHICLE BY PLATE
# =========================================================

def find_vehicle_by_plate(
    number_plate
):

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        WHERE number_plate = ?
    """, (
        number_plate,
    ))

    row = cursor.fetchone()

    connection.close()

    if row:

        return dict(row)

    return None


# =========================================================
# DATABASE INFORMATION
# =========================================================

def database_info():

    connection = connect()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM vehicles"
    )

    vehicle_count = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        "SELECT COUNT(*) FROM detections"
    )

    detection_count = (
        cursor.fetchone()[0]
    )

    connection.close()

    return {

        "vehicles":
            vehicle_count,

        "detections":
            detection_count
    }


# =========================================================
# DISPLAY VEHICLES
# =========================================================

def display_vehicles():

    vehicles = get_all_vehicles()

    print("\n" + "=" * 70)

    print(
        "VEHICLES STORED IN DATABASE"
    )

    print("=" * 70)

    if not vehicles:

        print(
            "No vehicles found."
        )

        return

    for vehicle in vehicles:

        print(

            f"{vehicle['vehicle_id']} | "

            f"{vehicle['vehicle_type']} | "

            f"{vehicle['color']} | "

            f"Plate: "
            f"{vehicle['number_plate']} | "

            f"Tracking: "
            f"{vehicle['tracking_id']}"
        )

    print("-" * 70)


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)

    print(
        "       VEHICLE DATABASE SYSTEM"
    )

    print("=" * 60)

    # -----------------------------------------------------
    # CREATE DATABASE TABLES
    # -----------------------------------------------------

    create_tables()

    print(
        "\nDatabase tables ready."
    )

    # -----------------------------------------------------
    # IMPORT VEHICLE IDENTITIES
    # -----------------------------------------------------

    print(
        "\nImporting vehicle identities..."
    )

    vehicle_count = (
        import_vehicle_identities()
    )

    print(
        f"Vehicles imported: "
        f"{vehicle_count}"
    )

    # -----------------------------------------------------
    # IMPORT TRACKING DATA
    # -----------------------------------------------------

    print(
        "\nImporting tracking detections..."
    )

    detection_count = (
        import_tracking_records()
    )

    print(
        f"Detections imported: "
        f"{detection_count}"
    )

    # -----------------------------------------------------
    # DATABASE INFORMATION
    # -----------------------------------------------------

    info = database_info()

    print("\n" + "=" * 60)

    print(
        "VEHICLE DATABASE READY"
    )

    print("=" * 60)

    print(
        f"Vehicles stored   : "
        f"{info['vehicles']}"
    )

    print(
        f"Detections stored : "
        f"{info['detections']}"
    )

    print(
        "\nDatabase:"
    )

    print(
        DATABASE_PATH
    )

    print("=" * 60)

    # -----------------------------------------------------
    # DISPLAY STORED VEHICLES
    # -----------------------------------------------------

    display_vehicles()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()