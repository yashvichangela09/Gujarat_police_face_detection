"""
pipeline_core.py

Complete Sentinel vehicle + license plate recognition pipeline.

Pipeline:
    Vehicle YOLO detection
        ↓
    Vehicle tracking / Re-ID
        ↓
    Vehicle attributes
        ↓
    License plate YOLO detection
        ↓
    PaddleOCR
        ↓
    Database + JSON + annotated video
"""

import os
import sys

# Ensure PyTorch C++ runtime loads first on Windows before Paddle to avoid DLL collisions
try:
    import torch
except Exception:
    pass

# Disable oneDNN/MKLDNN by default in PaddleX to avoid pir::DoubleAttribute executor bug on Windows
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"

import cv2
import json
import re
import glob
import numpy as np
import threading
from datetime import datetime


# =============================================================================
# VEHICLE ATTRIBUTES
# =============================================================================

from vehicle_attributes import (
    get_vehicle_type,
    get_vehicle_color,
    get_appearance_features,
)


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

CROP_DIR = os.path.join(
    OUTPUT_DIR,
    "vehicle_crops"
)

PLATE_CROP_DIR = os.path.join(
    OUTPUT_DIR,
    "plate_crops"
)


# =============================================================================
# MODEL PATHS
# =============================================================================

YOLO_MODEL = os.path.join(
    BASE_DIR,
    "yolo11n.pt"
)

PLATE_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "license-plate-finetune-v1n.pt"
)


# =============================================================================
# CREATE DIRECTORIES
# =============================================================================

for directory in (
    OUTPUT_DIR,
    CROP_DIR,
    PLATE_CROP_DIR,
):
    os.makedirs(
        directory,
        exist_ok=True
    )


# =============================================================================
# MODEL STATE
# =============================================================================

_model_lock = threading.RLock()

_vehicle_model = None
_plate_model = None
_ocr_engine = None
_ocr_attempted = False


# =============================================================================
# VEHICLE MODEL
# =============================================================================

def get_vehicle_model():

    global _vehicle_model

    if _vehicle_model is None:

        with _model_lock:

            if _vehicle_model is None:

                from ultralytics import YOLO

                if not os.path.exists(
                    YOLO_MODEL
                ):

                    raise FileNotFoundError(
                        "Vehicle YOLO model not found:\n"
                        + YOLO_MODEL
                    )

                print(
                    "\n[VEHICLE MODEL] Loading:"
                )

                print(
                    YOLO_MODEL
                )

                _vehicle_model = YOLO(
                    YOLO_MODEL
                )

                print(
                    "[VEHICLE MODEL] Loaded successfully."
                )

    return _vehicle_model


# =============================================================================
# FIND LICENSE PLATE MODEL
# =============================================================================

def find_plate_model():

    # -------------------------------------------------------------------------
    # Exact expected path
    # -------------------------------------------------------------------------

    if os.path.isfile(
        PLATE_MODEL
    ):

        print(
            "\n[PLATE MODEL] Found:"
        )

        print(
            PLATE_MODEL
        )

        return PLATE_MODEL

    alt_plate = PLATE_MODEL.replace(".pt", " .pt")
    if os.path.isfile(alt_plate):

        print(
            "\n[PLATE MODEL] Found (spaced):"
        )

        print(
            alt_plate
        )

        return alt_plate


    # -------------------------------------------------------------------------
    # Search recursively
    # -------------------------------------------------------------------------

    search_patterns = [

        os.path.join(
            BASE_DIR,
            "**",
            "*license*plate*.pt"
        ),

        os.path.join(
            BASE_DIR,
            "**",
            "*plate*.pt"
        ),

        os.path.join(
            BASE_DIR,
            "**",
            "*.pt"
        ),

    ]


    candidates = []


    for pattern in search_patterns:

        try:

            matches = glob.glob(
                pattern,
                recursive=True
            )

            for path in matches:

                if os.path.isfile(
                    path
                ):

                    path = os.path.normpath(
                        path
                    )

                    if path not in candidates:

                        candidates.append(
                            path
                        )

        except Exception:

            pass


    # -------------------------------------------------------------------------
    # Prefer plate model
    # -------------------------------------------------------------------------

    for path in candidates:

        filename = os.path.basename(
            path
        ).lower()

        if "plate" in filename:

            print(
                "\n[PLATE MODEL] Auto-found:"
            )

            print(
                path
            )

            return path


    print(
        "\n[PLATE MODEL] ERROR"
    )

    print(
        "License plate YOLO model could not be found."
    )

    print(
        "Expected:"
    )

    print(
        PLATE_MODEL
    )

    return None


# =============================================================================
# PLATE MODEL
# =============================================================================

def get_plate_model():

    global _plate_model

    if _plate_model is None:

        with _model_lock:

            if _plate_model is None:

                from ultralytics import YOLO

                model_path = find_plate_model()

                if model_path is None:

                    return None

                try:

                    print(
                        "\n[PLATE MODEL] Loading model..."
                    )

                    _plate_model = YOLO(
                        model_path
                    )

                    print(
                        "[PLATE MODEL] Loaded successfully."
                    )

                    try:

                        print(
                            "[PLATE MODEL] Classes:",
                            _plate_model.names
                        )

                    except Exception:

                        pass

                except Exception as e:

                    print(
                        "[PLATE MODEL] FAILED TO LOAD:"
                    )

                    print(
                        str(e)
                    )

                    _plate_model = None

    return _plate_model


# =============================================================================
# OCR
# =============================================================================

def get_ocr():

    global _ocr_engine
    global _ocr_attempted

    if _ocr_engine is None and not _ocr_attempted:

        with _model_lock:

            if _ocr_engine is None and not _ocr_attempted:

                _ocr_attempted = True

                try:

                    from paddleocr import PaddleOCR

                    print(
                        "\n[OCR] Loading PaddleOCR..."
                    )

                    _ocr_engine = PaddleOCR(
                        lang="en"
                    )

                    print(
                        "[OCR] PaddleOCR loaded successfully."
                    )

                except Exception as e:

                    print(
                        "\n[OCR] Could not load PaddleOCR:"
                    )

                    print(
                        str(e)
                    )

                    _ocr_engine = None

    return _ocr_engine


# =============================================================================
# VEHICLE ID
# =============================================================================

_next_id = 1

_id_lock = threading.Lock()


def _new_vehicle_id():

    global _next_id

    with _id_lock:

        vehicle_id = (
            f"VEH_{_next_id:04d}"
        )

        _next_id += 1

        return vehicle_id


def reset_id_counter(
    start=1
):

    global _next_id

    with _id_lock:

        _next_id = start


# =============================================================================
# TRACKING
# =============================================================================

_tracks = {}


def reset_tracker():

    global _tracks
    global _next_id

    _tracks = {}

    _next_id = 1


# =============================================================================
# TEXT CLEANING
# =============================================================================

def _clean_plate(
    text
):

    if not text:

        return "UNKNOWN"


    text = str(
        text
    ).upper()


    # Keep only letters and numbers

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )


    if not text:

        return "UNKNOWN"


    return text


# =============================================================================
# APPEARANCE FEATURE
# =============================================================================

def _feature(
    crop
):

    if (
        crop is None
        or crop.size == 0
    ):

        return None


    try:

        small = cv2.resize(
            crop,
            (64, 64)
        )


        hsv = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2HSV
        )


        hist = cv2.calcHist(
            [hsv],
            [0, 1],
            None,
            [16, 16],
            [0, 180, 0, 256]
        )


        hist = cv2.normalize(
            hist,
            hist
        )


        return hist.flatten()


    except Exception:

        return None


# =============================================================================
# SIMILARITY
# =============================================================================

def _similarity(
    f1,
    f2
):

    if (
        f1 is None
        or f2 is None
    ):

        return 0.0


    try:

        return float(
            cv2.compareHist(
                f1.astype(
                    np.float32
                ),
                f2.astype(
                    np.float32
                ),
                cv2.HISTCMP_CORREL
            )
        )

    except Exception:

        return 0.0


# =============================================================================
# TRACK SETTINGS
# =============================================================================

MATCH_DIST = 150
MATCH_SIM = 0.55
MAX_MISSING = 60


# =============================================================================
# FIND TRACK
# =============================================================================

def _find_track(
    feature,
    vtype,
    center
):

    best_id = None

    best_score = 0.0


    for vid, track in list(
        _tracks.items()
    ):

        if (
            track["vehicle_type"]
            != vtype
        ):

            continue


        old_center = np.array(
            track["center"],
            dtype=np.float32
        )


        new_center = np.array(
            center,
            dtype=np.float32
        )


        distance = float(
            np.linalg.norm(
                new_center
                - old_center
            )
        )


        if distance > MATCH_DIST:

            continue


        similarity = _similarity(
            feature,
            track["feature"]
        )


        if similarity > best_score:

            best_score = similarity

            best_id = vid


    if best_score >= MATCH_SIM:

        return best_id


    return None


# =============================================================================
# OCR PLATE
# =============================================================================

def _ocr_plate(
    plate_crop
):

    """
    Returns:
        plate_text
        plate_confidence
    """

    ocr = get_ocr()


    if (
        ocr is None
        or plate_crop is None
        or plate_crop.size == 0
    ):

        return (
            "UNKNOWN",
            0.0
        )


    processed_variants = []


    # -------------------------------------------------------------------------
    # Original + enlarged/sharpened versions
    # -------------------------------------------------------------------------

    try:

        crop = plate_crop.copy()


        if crop.shape[1] < 300:

            scale = max(
                2,
                min(
                    5,
                    int(
                        300
                        / max(
                            1,
                            crop.shape[1]
                        )
                    )
                )
            )


            crop = cv2.resize(
                crop,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )


        gray = cv2.cvtColor(
            crop,
            cv2.COLOR_BGR2GRAY
        )


        gray = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        ).apply(
            gray
        )


        blurred = cv2.GaussianBlur(
            gray,
            (0, 0),
            1.0
        )


        sharp = cv2.addWeighted(
            gray,
            1.5,
            blurred,
            -0.5,
            0
        )


        processed_variants = [
            crop,
            sharp
        ]


    except Exception:

        processed_variants = [
            plate_crop
        ]


    # -------------------------------------------------------------------------
    # OCR each variant
    # -------------------------------------------------------------------------

    best_text = "UNKNOWN"

    best_conf = 0.0


    for variant in processed_variants:

        temp_path = None


        try:

            import tempfile


            with tempfile.NamedTemporaryFile(
                suffix=".jpg",
                delete=False
            ) as tmp:

                temp_path = tmp.name


            cv2.imwrite(
                temp_path,
                variant
            )


            result = ocr.predict(
                temp_path
            )


            if not result:

                continue


            texts = []
            scores = []


            try:

                data = result[0]


                if hasattr(
                    data,
                    "get"
                ):

                    texts = data.get(
                        "rec_texts",
                        []
                    )


                    scores = data.get(
                        "rec_scores",
                        []
                    )

                elif isinstance(data, list):

                    for item in data:

                        if isinstance(item, (list, tuple)) and len(item) >= 2:

                            ts = item[1]

                            if isinstance(ts, (list, tuple)) and len(ts) >= 2:

                                texts.append(ts[0])

                                scores.append(ts[1])

            except Exception:

                pass


            if texts:

                combined = _clean_plate(
                    "".join(
                        str(x)
                        for x in texts
                    )
                )


                if combined == "UNKNOWN":

                    continue


                confidence = 0.0


                if scores:

                    try:

                        confidence = (
                            float(
                                max(scores)
                            )
                            * 100
                        )

                    except Exception:

                        confidence = 0.0


                if (
                    confidence
                    > best_conf
                ):

                    best_text = combined

                    best_conf = confidence

                    if best_conf >= 65.0:
                        break


        except Exception as e:

            print(
                f"[OCR ERROR] {e}"
            )


        finally:

            if temp_path:

                try:

                    os.unlink(
                        temp_path
                    )

                except Exception:

                    pass


    return (
        best_text,
        round(
            best_conf,
            2
        )
    )


# =============================================================================
# LICENSE PLATE DETECTION
# =============================================================================

def _detect_plate(
    vehicle_crop,
    vehicle_id
):

    """
    Detect a license plate inside a vehicle crop.

    Returns:
        plate_text
        plate_confidence
        plate_crop_path
    """


    plate_model = get_plate_model()


    if (
        plate_model is None
        or vehicle_crop is None
        or vehicle_crop.size == 0
    ):

        return (
            "UNKNOWN",
            0.0,
            None
        )


    try:

        # ---------------------------------------------------------------------
        # Plate detection
        # ---------------------------------------------------------------------

        results = plate_model.predict(
            vehicle_crop,
            conf=0.10,
            imgsz=1280,
            verbose=False
        )


        if not results:

            return (
                "UNKNOWN",
                0.0,
                None
            )


        best_box = None

        best_conf = 0.0


        # ---------------------------------------------------------------------
        # Highest confidence plate
        # ---------------------------------------------------------------------

        for result in results:

            if result.boxes is None:

                continue


            for box in result.boxes:

                try:

                    confidence = float(
                        box.conf[0].item()
                    )

                except Exception:

                    confidence = 0.0


                if (
                    confidence
                    > best_conf
                ):

                    best_conf = confidence

                    best_box = box


        if best_box is None:

            return (
                "UNKNOWN",
                0.0,
                None
            )


        # ---------------------------------------------------------------------
        # Bounding box
        # ---------------------------------------------------------------------

        x1, y1, x2, y2 = (
            best_box
            .xyxy[0]
            .cpu()
            .numpy()
            .astype(int)
        )


        h, w = vehicle_crop.shape[:2]


        # Padding for OCR

        pad_x = 12
        pad_y = 12


        x1 = max(
            0,
            x1 - pad_x
        )

        y1 = max(
            0,
            y1 - pad_y
        )

        x2 = min(
            w,
            x2 + pad_x
        )

        y2 = min(
            h,
            y2 + pad_y
        )


        if (
            x2 <= x1
            or y2 <= y1
        ):

            return (
                "UNKNOWN",
                0.0,
                None
            )


        plate_crop = vehicle_crop[
            y1:y2,
            x1:x2
        ]


        if plate_crop.size == 0:

            return (
                "UNKNOWN",
                0.0,
                None
            )


        # ---------------------------------------------------------------------
        # Save plate crop
        # ---------------------------------------------------------------------

        plate_path = os.path.join(
            PLATE_CROP_DIR,
            f"{vehicle_id}_plate.jpg"
        )


        cv2.imwrite(
            plate_path,
            plate_crop
        )


        print(
            f"[PLATE DETECTED] "
            f"{vehicle_id} | "
            f"Detector: "
            f"{best_conf * 100:.1f}%"
        )


        # ---------------------------------------------------------------------
        # OCR
        # ---------------------------------------------------------------------

        plate_text, ocr_conf = _ocr_plate(
            plate_crop
        )


        print(
            f"[PLATE OCR] "
            f"{vehicle_id} | "
            f"{plate_text} | "
            f"OCR: "
            f"{ocr_conf:.1f}%"
        )


        return (
            plate_text,
            ocr_conf,
            plate_path
        )


    except Exception as e:

        print(
            f"[PLATE ERROR] "
            f"{vehicle_id}: {e}"
        )


        return (
            "UNKNOWN",
            0.0,
            None
        )


# =============================================================================
# MAIN FRAME PROCESSING
# =============================================================================

def process_frame(
    frame,
    frame_number=0,
    run_plate=True,
    source_name="live"
):

    """
    Process one frame.

    Returns:
        list of vehicle detections
    """


    model = get_vehicle_model()


    # -------------------------------------------------------------------------
    # Vehicle detection
    # -------------------------------------------------------------------------

    results = model.predict(
        frame,
        conf=0.35,
        classes=[2, 3, 5, 7],
        imgsz=640,
        verbose=False
    )


    detections = []


    h, w = frame.shape[:2]


    if not results:

        return detections


    # -------------------------------------------------------------------------
    # Loop through detected vehicles
    # -------------------------------------------------------------------------

    for box in results[0].boxes:

        try:

            class_id = int(
                box.cls[0].item()
            )


            confidence = float(
                box.conf[0].item()
            )


            x1, y1, x2, y2 = (
                box.xyxy[0]
                .cpu()
                .numpy()
                .astype(int)
            )


        except Exception:

            continue


        # ---------------------------------------------------------------------
        # Clamp coordinates
        # ---------------------------------------------------------------------

        x1 = max(
            0,
            x1
        )

        y1 = max(
            0,
            y1
        )

        x2 = min(
            w,
            x2
        )

        y2 = min(
            h,
            y2
        )


        if (
            x2 <= x1
            or y2 <= y1
        ):

            continue


        # ---------------------------------------------------------------------
        # Vehicle crop
        # ---------------------------------------------------------------------

        crop = frame[
            y1:y2,
            x1:x2
        ]


        if crop.size == 0:

            continue


        # ---------------------------------------------------------------------
        # Vehicle type
        # ---------------------------------------------------------------------

        try:

            vtype = get_vehicle_type(
                class_id,
                crop
            )

        except Exception:

            try:

                vtype = get_vehicle_type(
                    class_id
                )

            except Exception:

                vtype = "Unknown"


        # ---------------------------------------------------------------------
        # Vehicle color
        # ---------------------------------------------------------------------

        try:

            color = get_vehicle_color(
                crop
            )

        except Exception:

            color = "Unknown"


        # ---------------------------------------------------------------------
        # Appearance feature
        # ---------------------------------------------------------------------

        feature = _feature(
            crop
        )


        center = (
            int(
                (x1 + x2) / 2
            ),
            int(
                (y1 + y2) / 2
            )
        )


        # ---------------------------------------------------------------------
        # Tracking
        # ---------------------------------------------------------------------

        vehicle_id = _find_track(
            feature,
            vtype,
            center
        )


        is_new = (
            vehicle_id is None
        )


        if is_new:

            vehicle_id = _new_vehicle_id()


            _tracks[
                vehicle_id
            ] = {

                "vehicle_type":
                    vtype,

                "feature":
                    feature,

                "center":
                    center,

                "last_frame":
                    frame_number,

                "missing_since":
                    None,

                "color":
                    color,

                "number_plate":
                    "UNKNOWN",

                "plate_conf":
                    0.0,

                "frames_seen":
                    0,
            }


        else:

            track = _tracks[
                vehicle_id
            ]


            track[
                "center"
            ] = center


            track[
                "last_frame"
            ] = frame_number


            track[
                "feature"
            ] = feature


            track[
                "missing_since"
            ] = None


            if (
                color
                not in (
                    "Unknown",
                    "Grey"
                )
                or track["color"]
                == "Unknown"
            ):

                track[
                    "color"
                ] = color


        # ---------------------------------------------------------------------
        # Increment frame count
        # ---------------------------------------------------------------------

        _tracks[
            vehicle_id
        ][
            "frames_seen"
        ] = (

            _tracks[
                vehicle_id
            ].get(
                "frames_seen",
                0
            )

            + 1
        )


        # ---------------------------------------------------------------------
        # Save vehicle crop
        # ---------------------------------------------------------------------

        crop_path = os.path.join(
            CROP_DIR,
            f"{vehicle_id}.jpg"
        )


        if not os.path.exists(
            crop_path
        ):

            cv2.imwrite(
                crop_path,
                crop
            )


        else:

            existing = cv2.imread(
                crop_path
            )


            if existing is not None:

                new_area = (
                    crop.shape[0]
                    * crop.shape[1]
                )


                old_area = (
                    existing.shape[0]
                    * existing.shape[1]
                )


                if new_area > old_area:

                    cv2.imwrite(
                        crop_path,
                        crop
                    )


        # ---------------------------------------------------------------------
        # Existing plate information
        # ---------------------------------------------------------------------

        plate_text = _tracks[
            vehicle_id
        ].get(
            "number_plate",
            "UNKNOWN"
        )


        plate_conf = _tracks[
            vehicle_id
        ].get(
            "plate_conf",
            0.0
        )


        # ---------------------------------------------------------------------
        # Plate detection
        #
        # New vehicle -> immediately
        #
        # Existing vehicle -> every 10 frames
        # ---------------------------------------------------------------------

        if run_plate and (
            is_new
            or frame_number % 10 == 0
        ):

            pt, pc, plate_path = (
                _detect_plate(
                    crop,
                    vehicle_id
                )
            )


            # -------------------------------------------------------------
            # Keep the best OCR result
            # -------------------------------------------------------------

            if pt not in (
                "UNKNOWN",
                ""
            ):

                if (
                    plate_text
                    == "UNKNOWN"
                    or pc > plate_conf
                ):

                    plate_text = pt

                    plate_conf = pc


                    _tracks[
                        vehicle_id
                    ][
                        "number_plate"
                    ] = pt


                    _tracks[
                        vehicle_id
                    ][
                        "plate_conf"
                    ] = pc


        # ---------------------------------------------------------------------
        # Appearance features
        # ---------------------------------------------------------------------

        try:

            appearance = (
                get_appearance_features(
                    crop
                )
            )

        except Exception:

            appearance = {}


        # ---------------------------------------------------------------------
        # Detection dictionary
        # ---------------------------------------------------------------------

        detection = {

            "vehicle_id":
                vehicle_id,

            "vehicle_type":
                vtype,

            "color":
                color,

            "number_plate":
                plate_text,

            "plate_confidence":
                plate_conf,

            "detection_confidence":
                round(
                    confidence * 100,
                    2
                ),

            "bbox": [
                int(x1),
                int(y1),
                int(x2),
                int(y2)
            ],

            "frame":
                frame_number,

            "source":
                source_name,

            "appearance":
                appearance,

            "plate_crop":
                plate_path
                if "plate_path" in locals()
                else None,

            "timestamp":
                datetime.now().isoformat(),
        }


        detections.append(
            detection
        )


    # -------------------------------------------------------------------------
    # Remove stale tracks
    # -------------------------------------------------------------------------

    stale_ids = []


    for vid, track in list(
        _tracks.items()
    ):

        if (
            frame_number
            - track.get(
                "last_frame",
                frame_number
            )
            > MAX_MISSING
        ):

            stale_ids.append(
                vid
            )


    for vid in stale_ids:

        try:

            del _tracks[
                vid
            ]

        except KeyError:

            pass


    return detections


# =============================================================================
# ALIAS USED BY SERVER
# =============================================================================

def process_ai_frame(
    frame,
    frame_number=0,
    run_plate=True,
    source_name="live"
):

    return process_frame(
        frame,
        frame_number,
        run_plate,
        source_name
    )


# =============================================================================
# VEHICLE DETAILS
# =============================================================================

def get_vehicle_details(
    vehicle_id
):

    return dict(
        _tracks.get(
            vehicle_id,
            {}
        )
    )


# =============================================================================
# GET ALL TRACKS
# =============================================================================

def get_all_vehicle_details():

    return {
        vehicle_id:
            dict(track)

        for vehicle_id, track
        in _tracks.items()
    }


# =============================================================================
# FLUSH TRACK DATA
# =============================================================================

def flush_to_json(
    output_path=None
):

    if output_path is None:

        output_path = os.path.join(
            OUTPUT_DIR,
            "final_vehicle_records.json"
        )


    records = []


    for vehicle_id, track in (
        _tracks.items()
    ):

        record = dict(
            track
        )


        record[
            "vehicle_id"
        ] = vehicle_id


        records.append(
            record
        )


    try:

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                records,
                f,
                indent=2,
                default=str
            )


    except Exception as e:

        print(
            "[JSON ERROR]",
            e
        )


    return records


# =============================================================================
# RESET
# =============================================================================

def reset():

    reset_tracker()

    reset_id_counter(
        1
    )


# =============================================================================
# SIMPLE TEST
# =============================================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "SENTINEL pipeline_core.py"
    )

    print(
        "=" * 70
    )

    print(
        "Vehicle model:",
        YOLO_MODEL
    )

    print(
        "Plate model:",
        PLATE_MODEL
    )

    print(
        "Output:",
        OUTPUT_DIR
    )

    print(
        "=" * 70
    )