import json
import os


# =========================================================
# CONFIGURATION
# =========================================================

OUTPUT_DIR = "output"

VEHICLE_FILE = os.path.join(
    OUTPUT_DIR,
    "vehicle_records.json"
)

TRACKING_FILE = os.path.join(
    OUTPUT_DIR,
    "tracking_records.json"
)

IDENTITY_FILE = os.path.join(
    OUTPUT_DIR,
    "final_vehicle_records.json"
)


# =========================================================
# LOAD JSON
# =========================================================

def load_json(file_path):

    if not os.path.exists(file_path):
        return []

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"Error loading {file_path}: {e}"
        )

        return []


# =========================================================
# LOAD ALL DATA
# =========================================================

def load_vehicle_data():

    return load_json(
        VEHICLE_FILE
    )


def load_tracking_data():

    return load_json(
        TRACKING_FILE
    )


def load_identity_data():

    return load_json(
        IDENTITY_FILE
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("          VEHICLE DATA LOADER")
    print("=" * 60)

    vehicles = load_vehicle_data()
    tracking = load_tracking_data()
    identities = load_identity_data()

    print(
        f"\nVehicle records  : {len(vehicles)}"
    )

    print(
        f"Tracking records : {len(tracking)}"
    )

    print(
        f"Vehicle identities: {len(identities)}"
    )

    print("\nData loading completed.")

    print("=" * 60)