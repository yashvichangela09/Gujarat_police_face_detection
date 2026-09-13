from ultralytics import YOLO
from paddleocr import PaddleOCR
import cv2
import re
import os
import json
import numpy as np


# =========================================================
# AI VEHICLE RECOGNITION - FINAL INTEGRATED PIPELINE
# =========================================================

print("=" * 60)
print("       AI VEHICLE RECOGNITION SYSTEM")
print("=" * 60)


# =========================================================
# SETTINGS
# =========================================================

INPUT_IMAGE = "input/images/test.jpg"

OUTPUT_DIR = "output"

OUTPUT_IMAGE = "output/final_result.jpg"

OUTPUT_JSON = "output/final_vehicle_records.json"

VEHICLE_MODEL = "yolo11n.pt"

PLATE_MODEL = "models/license-plate-finetune-v1n.pt"


# =========================================================
# CREATE OUTPUT FOLDER
# =========================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# =========================================================
# LOAD MODELS
# =========================================================

print("\nLoading models...")

vehicle_model = YOLO(
    VEHICLE_MODEL
)

plate_model = YOLO(
    PLATE_MODEL
)

ocr = PaddleOCR(
    lang="en"
)

print("Models loaded.")


# =========================================================
# VEHICLE CLASSES
# =========================================================

VEHICLE_CLASSES = {

    2: "Car",

    3: "Motorcycle",

    5: "Bus",

    7: "Truck"
}


# =========================================================
# VEHICLE TYPE
# =========================================================

def get_vehicle_type(class_id):

    return VEHICLE_CLASSES.get(
        class_id,
        "Vehicle"
    )


# =========================================================
# COLOR DETECTION
# =========================================================

def detect_color(image):

    if image is None or image.size == 0:

        return "Unknown"


    image = cv2.resize(
        image,
        (100, 100)
    )


    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )


    h = hsv[:, :, 0]

    s = hsv[:, :, 1]

    v = hsv[:, :, 2]


    mean_s = np.mean(s)

    mean_v = np.mean(v)


    # -----------------------------------------------------
    # BLACK
    # -----------------------------------------------------

    if mean_v < 60:

        return "Black"


    # -----------------------------------------------------
    # WHITE
    # -----------------------------------------------------

    if mean_s < 45 and mean_v > 170:

        return "White"


    # -----------------------------------------------------
    # GREY
    # -----------------------------------------------------

    if (
        mean_s < 55
        and 80 < mean_v < 180
    ):

        return "Grey"


    # -----------------------------------------------------
    # COLORED PIXELS
    # -----------------------------------------------------

    valid_pixels = hsv[
        (s > 60) &
        (v > 60)
    ]


    if len(valid_pixels) == 0:

        return "Unknown"


    mean_hue = np.mean(
        valid_pixels[:, 0]
    )


    # -----------------------------------------------------
    # COLOR
    # -----------------------------------------------------

    if mean_hue < 10 or mean_hue >= 170:

        return "Red"

    elif mean_hue < 25:

        return "Orange"

    elif mean_hue < 35:

        return "Yellow"

    elif mean_hue < 85:

        return "Green"

    elif mean_hue < 130:

        return "Blue"

    elif mean_hue < 160:

        return "Purple"


    return "Unknown"


# =========================================================
# APPEARANCE FEATURES
# =========================================================

def get_appearance_features(image):

    if image is None or image.size == 0:

        return {}


    height, width = image.shape[:2]


    aspect_ratio = round(
        width / height,
        2
    ) if height > 0 else 0


    return {

        "aspect_ratio":
            aspect_ratio,

        "image_width":
            width,

        "image_height":
            height

    }


# =========================================================
# LOAD ORIGINAL IMAGE
# =========================================================

image = cv2.imread(
    INPUT_IMAGE
)


if image is None:

    print(
        "\nERROR: Could not find input image:"
    )

    print(INPUT_IMAGE)

    exit()


final_image = image.copy()


# =========================================================
# VEHICLE DETECTION
# =========================================================

print("\n[1] Detecting vehicles...")


vehicle_results = vehicle_model(
    image,
    classes=[2, 3, 5, 7],
    conf=0.35,
    iou=0.45,
    imgsz=1280,
    verbose=False
)


# =========================================================
# STORAGE
# =========================================================

vehicle_records = []

vehicle_count = 0

plate_count = 0


# =========================================================
# PROCESS VEHICLES
# =========================================================

for result in vehicle_results:

    if result.boxes is None:

        continue


    for box in result.boxes:

        vehicle_count += 1


        # -------------------------------------------------
        # VEHICLE CLASS
        # -------------------------------------------------

        class_id = int(
            box.cls[0].item()
        )


        vehicle_type = get_vehicle_type(
            class_id
        )


        # -------------------------------------------------
        # VEHICLE CONFIDENCE
        # -------------------------------------------------

        vehicle_confidence = float(
            box.conf[0].item()
        )


        # -------------------------------------------------
        # VEHICLE BOX
        # -------------------------------------------------

        vx1, vy1, vx2, vy2 = (

            box.xyxy[0]
            .cpu()
            .numpy()
            .astype(int)

        )


        vx1 = max(
            0,
            vx1
        )

        vy1 = max(
            0,
            vy1
        )

        vx2 = min(
            image.shape[1],
            vx2
        )

        vy2 = min(
            image.shape[0],
            vy2
        )


        if vx2 <= vx1 or vy2 <= vy1:

            continue


        # -------------------------------------------------
        # VEHICLE CROP
        # -------------------------------------------------

        vehicle_crop = image[
            vy1:vy2,
            vx1:vx2
        ]


        if vehicle_crop.size == 0:

            continue


        # -------------------------------------------------
        # VEHICLE COLOR
        # -------------------------------------------------

        color = detect_color(
            vehicle_crop
        )


        # -------------------------------------------------
        # APPEARANCE
        # -------------------------------------------------

        appearance = get_appearance_features(
            vehicle_crop
        )


        # -------------------------------------------------
        # VEHICLE ID
        # -------------------------------------------------

        vehicle_id = (
            f"VEH_{vehicle_count:04d}"
        )


        # -------------------------------------------------
        # DEFAULT PLATE INFORMATION
        # -------------------------------------------------

        plate_number = "UNKNOWN"

        plate_confidence = 0

        plate_box_found = False


        # =================================================
        # NUMBER PLATE DETECTION
        # =================================================

        plate_results = plate_model(
            vehicle_crop,
            conf=0.25,
            verbose=False
        )


        for plate_result in plate_results:

            if plate_result.boxes is None:

                continue


            for plate_box in plate_result.boxes:

                plate_count += 1

                plate_box_found = True


                # -----------------------------------------
                # PLATE COORDINATES
                # -----------------------------------------

                px1, py1, px2, py2 = (

                    plate_box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)

                )


                # Convert crop coordinates
                # to original image coordinates

                px1 += vx1
                px2 += vx1

                py1 += vy1
                py2 += vy1


                px1 = max(
                    0,
                    px1
                )

                py1 = max(
                    0,
                    py1
                )

                px2 = min(
                    image.shape[1],
                    px2
                )

                py2 = min(
                    image.shape[0],
                    py2
                )


                if (
                    px2 <= px1
                    or py2 <= py1
                ):

                    continue


                # -----------------------------------------
                # PLATE CROP
                # -----------------------------------------

                plate_crop = image[
                    py1:py2,
                    px1:px2
                ]


                if plate_crop.size == 0:

                    continue


                # =========================================
                # OCR
                # =========================================

                try:

                    ocr_result = ocr.predict(
                        plate_crop
                    )


                    rec_texts = (
                        ocr_result[0]["rec_texts"]
                    )

                    rec_scores = (
                        ocr_result[0]["rec_scores"]
                    )


                    if rec_texts:

                        text = "".join(
                            rec_texts
                        )


                        text = text.upper()


                        text = re.sub(
                            r"[^A-Z0-9]",
                            "",
                            text
                        )


                        plate_number = text


                        if rec_scores:

                            plate_confidence = (
                                max(rec_scores) * 100
                            )

                    else:

                        plate_number = "UNKNOWN"


                except Exception:

                    plate_number = "UNKNOWN"

                    plate_confidence = 0


                # -----------------------------------------
                # DRAW PLATE BOX
                # -----------------------------------------

                cv2.rectangle(

                    final_image,

                    (px1, py1),

                    (px2, py2),

                    (0, 255, 0),

                    3

                )


                # -----------------------------------------
                # PLATE LABEL
                # -----------------------------------------

                plate_label = (

                    f"{plate_number} "
                    f"({plate_confidence:.0f}%)"

                )


                cv2.putText(

                    final_image,

                    plate_label,

                    (
                        px1,
                        max(
                            25,
                            py1 - 10
                        )
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 255, 0),

                    2

                )


                # Only use the first plate
                # for this vehicle

                break


        # =================================================
        # VEHICLE BOX
        # =================================================

        cv2.rectangle(

            final_image,

            (vx1, vy1),

            (vx2, vy2),

            (255, 0, 0),

            2

        )


        # =================================================
        # VEHICLE LABEL
        # =================================================

        label = (

            f"{vehicle_id} | "
            f"{vehicle_type} | "
            f"{color}"

        )


        cv2.putText(

            final_image,

            label,

            (
                vx1,
                max(
                    20,
                    vy1 - 10
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            (255, 0, 0),

            2

        )


        # =================================================
        # VEHICLE RECORD
        # =================================================

        vehicle_record = {

            "vehicle_id":
                vehicle_id,

            "vehicle_type":
                vehicle_type,

            "color":
                color,

            "vehicle_confidence":
                round(
                    vehicle_confidence * 100,
                    2
                ),

            "number_plate":
                plate_number,

            "plate_confidence":
                round(
                    plate_confidence,
                    2
                ),

            "plate_detected":
                plate_box_found,

            "bounding_box": {

                "x1": int(vx1),

                "y1": int(vy1),

                "x2": int(vx2),

                "y2": int(vy2)

            },

            "appearance":
                appearance

        }


        vehicle_records.append(
            vehicle_record
        )


# =========================================================
# SAVE FINAL IMAGE
# =========================================================

cv2.imwrite(

    OUTPUT_IMAGE,

    final_image

)


# =========================================================
# SAVE FINAL JSON
# =========================================================

with open(

    OUTPUT_JSON,

    "w",

    encoding="utf-8"

) as file:

    json.dump(

        vehicle_records,

        file,

        indent=4

    )


# =========================================================
# TERMINAL OUTPUT
# =========================================================

print("\n" + "=" * 60)

print("                 FINAL RESULT")

print("=" * 60)

print(
    f"Vehicles detected : {vehicle_count}"
)

print(
    f"Plates detected   : {plate_count}"
)

print(
    f"Saved image       : {OUTPUT_IMAGE}"
)

print(
    f"Saved records     : {OUTPUT_JSON}"
)

print("=" * 60)


print("\nVEHICLE INFORMATION")

print("-" * 60)


for vehicle in vehicle_records:

    print(

        f"{vehicle['vehicle_id']} | "
        f"{vehicle['vehicle_type']} | "
        f"{vehicle['color']} | "
        f"Plate: {vehicle['number_plate']}"

    )


print("=" * 60)