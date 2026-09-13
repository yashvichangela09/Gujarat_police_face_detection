import json
import os
import sys
import cv2
from datetime import datetime

# Add parent dir so vehicle_attributes is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vehicle_attributes import get_vehicle_color


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CROP_DIR   = os.path.join(BASE_DIR, "output", "vehicle_crops")

INPUT_TRACKING = os.path.join(
    OUTPUT_DIR,
    "tracking_records.json"
)

INPUT_ATTRIBUTES = os.path.join(
    OUTPUT_DIR,
    "vehicle_records.json"
)

OUTPUT_IDENTITY = os.path.join(
    OUTPUT_DIR,
    "final_vehicle_records.json"
)


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path, default):

    if not os.path.exists(path):
        print(f"WARNING: File not found: {path}")
        return default

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(f"ERROR reading {path}: {e}")

        return default


# =========================================================
# CREATE VEHICLE IDENTITY
# =========================================================

def create_vehicle_identity(
    vehicle_id,
    vehicle_type="Unknown",
    color="Unknown",
    number_plate="UNKNOWN",
    plate_confidence=0,
    detection_confidence=0,
    tracking_id=None,
    appearance=None
):

    return {

        "vehicle_id": vehicle_id,

        "tracking_id": tracking_id,

        "vehicle_type": vehicle_type,

        "color": color,

        "number_plate": number_plate,

        "plate_confidence": plate_confidence,

        "detection_confidence": detection_confidence,

        "appearance": appearance or {},

        "last_updated":
            datetime.now().isoformat(
                timespec="seconds"
            )
    }


# =========================================================
# GET COLOR FROM SAVED CROP
# Falls back to reading the vehicle crop image directly
# when no color was recorded in tracking data.
# =========================================================

def get_color_from_crop(vehicle_id):

    extensions = [".jpg", ".jpeg", ".png"]

    for ext in extensions:

        path = os.path.join(CROP_DIR, vehicle_id + ext)

        if os.path.exists(path):

            img = cv2.imread(path)

            if img is not None and img.size > 0:
                return get_vehicle_color(img)

    return "Unknown"


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("       VEHICLE IDENTITY SYSTEM")
    print("=" * 60)


    # =====================================================
    # LOAD TRACKING DATA
    # =====================================================

    tracking_data = load_json(
        INPUT_TRACKING,
        []
    )


    # =====================================================
    # LOAD ATTRIBUTE DATA
    # =====================================================

    attribute_data = load_json(
        INPUT_ATTRIBUTES,
        []
    )


    print(
        f"\nTracking records loaded : "
        f"{len(tracking_data)}"
    )

    print(
        f"Attribute records loaded: "
        f"{len(attribute_data)}"
    )


    # =====================================================
    # ATTRIBUTE LOOKUP
    # =====================================================

    attributes_by_id = {}

    for vehicle in attribute_data:

        vehicle_id = vehicle.get(
            "vehicle_id"
        )

        if vehicle_id:

            attributes_by_id[
                vehicle_id
            ] = vehicle


    # =====================================================
    # TRACKING LOOKUP
    # Keeps the last observation per vehicle,
    # plus a majority-vote color across all frames.
    # =====================================================

    tracking_by_id = {}
    tracking_colors = {}  # vehicle_id -> list of colors seen

    for record in tracking_data:

        vehicle_id = record.get("vehicle_id")

        if vehicle_id is None:
            continue

        # Keep latest observation
        tracking_by_id[vehicle_id] = record

        # Collect colors for majority vote
        c = record.get("color")
        if c and c not in ("Unknown", ""):
            tracking_colors.setdefault(vehicle_id, []).append(c)


    # =====================================================
    # FINAL RECORDS
    # =====================================================

    final_records = []


    # =====================================================
    # CASE 1 — TRACKING DATA EXISTS
    # =====================================================

    if tracking_by_id:

        print(
            "\nCombining tracking + attributes..."
        )


        for index, (
            tracking_vehicle_id,
            tracking
        ) in enumerate(
            tracking_by_id.items(),
            start=1
        ):

            # -------------------------------------------------
            # Use the same vehicle ID from tracking
            # -------------------------------------------------

            vehicle_id = tracking_vehicle_id


            # -------------------------------------------------
            # Find matching attributes
            # -------------------------------------------------

            attribute = attributes_by_id.get(
                vehicle_id,
                {}
            )


            # -------------------------------------------------
            # Vehicle type
            # -------------------------------------------------

            vehicle_type = (

                tracking.get(
                    "vehicle_type"
                )

                or attribute.get(
                    "vehicle_type",
                    "Unknown"
                )
            )


            # -------------------------------------------------
            # Color
            # Priority:
            #   1. Majority vote across tracking frames
            #   2. Attributes file (static image)
            #   3. Last tracking record color field
            #   4. Direct color read from saved crop
            # -------------------------------------------------

            color_votes = tracking_colors.get(vehicle_id, [])

            if color_votes:
                from collections import Counter
                color = Counter(color_votes).most_common(1)[0][0]

            elif attribute.get("color") and attribute["color"] != "Unknown":
                color = attribute["color"]

            elif tracking.get("color") and tracking["color"] != "Unknown":
                color = tracking["color"]

            else:
                # Read directly from saved crop image
                color = get_color_from_crop(vehicle_id)


            # -------------------------------------------------
            # Appearance
            # -------------------------------------------------

            appearance = (
                attribute.get(
                    "appearance"
                )
                or attribute.get(
                    "appearance_features",
                    {}
                )
            )


            # -------------------------------------------------
            # Detection confidence
            # -------------------------------------------------

            detection_confidence = (

                tracking.get(
                    "confidence"
                )

                or attribute.get(
                    "detection_confidence",
                    0
                )
            )


            # -------------------------------------------------
            # Number plate
            #
            # OCR/plate information will be connected
            # during final integration.
            # -------------------------------------------------

            number_plate = (

                tracking.get(
                    "number_plate"
                )

                or attribute.get(
                    "number_plate",
                    "UNKNOWN"
                )
            )


            # -------------------------------------------------
            # Plate confidence
            # -------------------------------------------------

            plate_confidence = (

                tracking.get(
                    "plate_confidence"
                )

                or attribute.get(
                    "plate_confidence",
                    0
                )
            )


            # -------------------------------------------------
            # Tracking ID
            #
            # Currently our tracker uses vehicle_id
            # as the identity, so preserve it here.
            # -------------------------------------------------

            tracking_id = tracking.get(
                "tracking_id",
                vehicle_id
            )


            # -------------------------------------------------
            # Create final identity
            # -------------------------------------------------

            record = create_vehicle_identity(

                vehicle_id=vehicle_id,

                vehicle_type=vehicle_type,

                color=color,

                number_plate=number_plate,

                plate_confidence=plate_confidence,

                detection_confidence=
                    detection_confidence,

                tracking_id=tracking_id,

                appearance=appearance
            )


            final_records.append(
                record
            )


    # =====================================================
    # CASE 2 — NO TRACKING DATA
    # =====================================================

    elif attribute_data:

        print(
            "\nTracking data unavailable."
        )

        print(
            "Using attribute records directly..."
        )


        for index, vehicle in enumerate(
            attribute_data,
            start=1
        ):

            vehicle_id = (
                f"VEH_{index:04d}"
            )


            record = create_vehicle_identity(

                vehicle_id=vehicle_id,

                vehicle_type=vehicle.get(
                    "vehicle_type",
                    "Unknown"
                ),

                color=vehicle.get(
                    "color",
                    "Unknown"
                ),

                number_plate=vehicle.get(
                    "number_plate",
                    "UNKNOWN"
                ),

                plate_confidence=vehicle.get(
                    "plate_confidence",
                    0
                ),

                detection_confidence=vehicle.get(
                    "detection_confidence",
                    0
                ),

                tracking_id=vehicle.get(
                    "tracking_id"
                ),

                appearance=(
                    vehicle.get(
                        "appearance"
                    )
                    or vehicle.get(
                        "appearance_features",
                        {}
                    )
                )
            )


            final_records.append(
                record
            )


    # =====================================================
    # CASE 3 — NOTHING FOUND
    # =====================================================

    else:

        print(
            "\nNo tracking or attribute records found."
        )


    # =====================================================
    # SAVE FINAL IDENTITY
    # =====================================================

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    with open(
        OUTPUT_IDENTITY,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_records,
            file,
            indent=4
        )


    # =====================================================
    # DISPLAY RESULTS
    # =====================================================

    print("\n" + "=" * 60)
    print("FINAL VEHICLE IDENTITIES")
    print("=" * 60)


    for vehicle in final_records:

        print(
            f"{vehicle['vehicle_id']} | "
            f"{vehicle['vehicle_type']} | "
            f"{vehicle['color']} | "
            f"Plate: {vehicle['number_plate']} | "
            f"Track: {vehicle['tracking_id']}"
        )


    print("-" * 60)


    print(
        f"Final vehicle count: "
        f"{len(final_records)}"
    )


    print(
        "\nSaved to:"
    )


    print(
        OUTPUT_IDENTITY
    )


    print("=" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()