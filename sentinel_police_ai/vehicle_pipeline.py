import subprocess
import sys
import os


# =========================================================
# CONFIGURATION
# =========================================================

SCRIPTS = [

    # 1. Detect vehicles
    "vehicle_detection/detect_vehicle.py",

    # 2. Detect number plates
    "plate_detection/detect_plate.py",

    # 3. Read number plates
    "plate_detection/read_plate.py",

    # 4. Track vehicles
    "vehicle_tracking.py",

    # 5. Extract vehicle attributes
    "vehicle_attributes.py",

    # 6. Create vehicle identities
    "vehicle_identity.py",

    # 7. Generate report
    "vehicle_report.py"
]


# =========================================================
# RUN ONE COMPONENT
# =========================================================

def run_component(script):

    print()
    print("=" * 60)
    print(f"RUNNING: {script}")
    print("=" * 60)

    try:

        subprocess.run(
            [
                sys.executable,
                script
            ],
            check=True
        )

        print(
            f"\nCOMPLETED: {script}"
        )

    except subprocess.CalledProcessError:

        print(
            f"\nERROR: {script} failed."
        )

        return False

    return True


# =========================================================
# MAIN PIPELINE
# =========================================================

def main():

    print("=" * 60)
    print("       AI VEHICLE RECOGNITION SYSTEM")
    print("=" * 60)

    print(
        "\nStarting complete processing pipeline..."
    )

    print(
        "\nNo localhost / Streamlit required."
    )


    # -----------------------------------------------------
    # Check input image
    # -----------------------------------------------------

    input_image = "input/images/test.jpg"

    if not os.path.exists(input_image):

        print(
            f"\nERROR: Input image not found:"
        )

        print(input_image)

        return


    # -----------------------------------------------------
    # Run every component
    # -----------------------------------------------------

    completed = 0

    for script in SCRIPTS:

        if not os.path.exists(script):

            print(
                f"\nERROR: Component not found:"
            )

            print(script)

            return

        success = run_component(
            script
        )

        if not success:

            print(
                "\nPIPELINE STOPPED."
            )

            print(
                f"Failed component: {script}"
            )

            return

        completed += 1


    # =====================================================
    # COMPLETE
    # =====================================================

    print()
    print("=" * 60)
    print("          PIPELINE COMPLETED")
    print("=" * 60)

    print(
        f"Components completed: "
        f"{completed}/{len(SCRIPTS)}"
    )

    print()
    print("Main outputs:")

    print(
        "  output/image_result.jpg"
    )

    print(
        "  output/final_result.jpg"
    )

    print(
        "  output/tracking_records.json"
    )

    print(
        "  output/vehicle_records.json"
    )

    print(
        "  output/final_vehicle_records.json"
    )

    print(
        "  output/vehicle_database.db"
    )

    print(
        "  output/vehicle_report.json"
    )

    print(
        "  output/vehicle_report.csv"
    )

    print("=" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()