import cv2
import os
import json
from ultralytics import YOLO


# =========================================================
# SETTINGS
# =========================================================

INPUT_VIDEO = "input/videos/test.mp4"
OUTPUT_VIDEO = "output/video_result.mp4"

MODEL_PATH = "yolo11n.pt"

# Process ONLY 15 frames
NUM_FRAMES = 15

# Vehicle classes
# 2 = Car
# 3 = Motorcycle
# 5 = Bus
# 7 = Truck
VEHICLE_CLASSES = [2, 3, 5, 7]

CONFIDENCE = 0.35


# =========================================================
# CREATE OUTPUT FOLDER
# =========================================================

os.makedirs("output", exist_ok=True)


# =========================================================
# LOAD MODEL
# =========================================================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)


# =========================================================
# OPEN VIDEO
# =========================================================

cap = cv2.VideoCapture(INPUT_VIDEO)

if not cap.isOpened():
    print("ERROR: Could not open video!")
    exit()


# =========================================================
# VIDEO INFORMATION
# =========================================================

total_frames = int(
    cap.get(cv2.CAP_PROP_FRAME_COUNT)
)

fps = cap.get(
    cv2.CAP_PROP_FPS
)

width = int(
    cap.get(cv2.CAP_PROP_FRAME_WIDTH)
)

height = int(
    cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
)


print()
print("Video information:")
print(f"Total frames : {total_frames}")
print(f"FPS          : {fps}")
print(f"Resolution   : {width} x {height}")
print(f"Frames used  : {NUM_FRAMES}")
print()


# =========================================================
# SELECT 15 EVENLY SPACED FRAMES
# =========================================================

if total_frames <= NUM_FRAMES:

    frame_indices = list(
        range(total_frames)
    )

else:

    frame_indices = [
        int(i * (total_frames - 1) / (NUM_FRAMES - 1))
        for i in range(NUM_FRAMES)
    ]


# =========================================================
# VIDEO WRITER
# =========================================================

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)

out = cv2.VideoWriter(
    OUTPUT_VIDEO,
    fourcc,
    fps,
    (width, height)
)


# =========================================================
# VEHICLE RECORDS
# =========================================================

vehicle_records = []

vehicle_counter = 0


# =========================================================
# PROCESS 15 FRAMES
# =========================================================

for frame_number, frame_index in enumerate(
    frame_indices,
    start=1
):

    # Move directly to required frame
    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        frame_index
    )

    ret, frame = cap.read()

    if not ret:
        print(
            f"Could not read frame {frame_index}"
        )
        continue


    print(
        f"Processing frame {frame_number}/{len(frame_indices)} "
        f"(video frame {frame_index})..."
    )


    # =====================================================
    # DETECT VEHICLES
    # =====================================================

    results = model.predict(

        source=frame,

        classes=VEHICLE_CLASSES,

        conf=CONFIDENCE,

        imgsz=640,

        verbose=False
    )


    result = results[0]


    # =====================================================
    # PROCESS DETECTIONS
    # =====================================================

    if result.boxes is not None:

        for box in result.boxes:

            class_id = int(
                box.cls[0].item()
            )

            confidence = float(
                box.conf[0].item()
            )


            # -------------------------------------------------
            # BOX COORDINATES
            # -------------------------------------------------

            x1, y1, x2, y2 = (
                box.xyxy[0]
                .cpu()
                .numpy()
                .astype(int)
            )


            x1 = max(0, x1)
            y1 = max(0, y1)

            x2 = min(width, x2)
            y2 = min(height, y2)


            if x2 <= x1 or y2 <= y1:
                continue


            # -------------------------------------------------
            # VEHICLE TYPE
            # -------------------------------------------------

            vehicle_types = {

                2: "Car",
                3: "Motorcycle",
                5: "Bus",
                7: "Truck"
            }

            vehicle_type = vehicle_types.get(
                class_id,
                "Vehicle"
            )


            # -------------------------------------------------
            # VEHICLE ID
            # -------------------------------------------------

            vehicle_counter += 1

            vehicle_id = (
                f"VEH_{vehicle_counter:04d}"
            )


            # -------------------------------------------------
            # SAVE RECORD
            # -------------------------------------------------

            vehicle_records.append({

                "vehicle_id": vehicle_id,

                "frame": frame_index,

                "vehicle_type": vehicle_type,

                "detection_confidence":
                    round(
                        confidence * 100,
                        2
                    ),

                "bounding_box": {

                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                }

            })


            # =================================================
            # DRAW VEHICLE BOX
            # =================================================

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                (255, 0, 0),

                2
            )


            # =================================================
            # LABEL
            # =================================================

            label = (

                f"{vehicle_id} | "

                f"{vehicle_type} | "

                f"{confidence * 100:.0f}%"
            )


            cv2.putText(

                frame,

                label,

                (x1, max(25, y1 - 8)),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 0, 0),

                2,

                cv2.LINE_AA
            )


    # =====================================================
    # SHOW FRAME NUMBER
    # =====================================================

    cv2.putText(

        frame,

        f"Frame: {frame_number}/{len(frame_indices)}",

        (20, 40),

        cv2.FONT_HERSHEY_SIMPLEX,

        1,

        (0, 255, 0),

        2
    )


    # =====================================================
    # WRITE FRAME
    # =====================================================

    out.write(frame)


# =========================================================
# RELEASE
# =========================================================

cap.release()
out.release()


# =========================================================
# SAVE RECORDS
# =========================================================

with open(
    "output/video_vehicle_records.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        vehicle_records,
        f,
        indent=4
    )


# =========================================================
# COMPLETE
# =========================================================

print()
print("=" * 60)
print("VIDEO PROCESSING COMPLETE")
print("=" * 60)

print(
    f"Frames processed : {len(frame_indices)}"
)

print(
    f"Vehicle detections : {len(vehicle_records)}"
)

print()
print(
    f"Video result:"
)

print(
    OUTPUT_VIDEO
)

print()
print(
    "Vehicle records:"
)

print(
    "output/video_vehicle_records.json"
)

print("=" * 60)