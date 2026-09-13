"""
Run the SENTINEL AI pipeline against a local video.

The script automatically finds the CCTV video inside the project,
so no Windows video path needs to be typed in the terminal.
"""

import argparse
import functools
import json
import os
import sys
import time
from pathlib import Path

# Force immediate console flushing on Windows
print = functools.partial(print, flush=True)

# Ensure PyTorch C++ runtime loads first on Windows before Paddle to avoid DLL collisions
try:
    import torch
except Exception:
    pass

# Disable oneDNN/MKLDNN by default in PaddleX to avoid pir::DoubleAttribute executor bug on Windows
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"

import cv2


# ============================================================
# PROJECT SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import sentinel_db as db
import cross_camera_reid as reid
import sentinel_server as server


# ============================================================
# FIND VIDEO AUTOMATICALLY
# ============================================================

def find_video():

    preferred_name = "india_traffic.mp4"

    # First search for the exact expected video.
    matches = list(BASE_DIR.rglob(preferred_name))

    if matches:
        return matches[0].resolve()

    # If exact name is not found, search for any MP4.
    mp4_files = list(BASE_DIR.rglob("*.mp4"))

    # Ignore generated output video.
    mp4_files = [
        p for p in mp4_files
        if "output" not in p.parts
    ]

    if mp4_files:
        return mp4_files[0].resolve()

    return None


def resolve_video_path(video_arg=None):
    """
    Resolve video path from CLI argument or search automatically.
    Handles:
    - dummy_videos vs 'dummy videos' directory name differences
    - Absolute and relative paths
    - Stripping quotes/whitespace
    - Automatic project fallback search
    """
    if not video_arg:
        return find_video()

    clean = str(video_arg).strip().strip('"').strip("'")
    if not clean:
        return find_video()

    candidate_paths = [
        Path(clean),
        BASE_DIR / clean,
    ]

    # Handle dummy_videos vs 'dummy videos'
    if "dummy_videos" in clean:
        alt = clean.replace("dummy_videos", "dummy videos")
        candidate_paths.extend([Path(alt), BASE_DIR / alt])
    elif "dummy videos" in clean:
        alt = clean.replace("dummy videos", "dummy_videos")
        candidate_paths.extend([Path(alt), BASE_DIR / alt])

    # Check candidates
    for p in candidate_paths:
        try:
            resolved = p.expanduser().resolve()
            if resolved.is_file():
                return resolved
        except Exception:
            pass

    # Try matching filename anywhere in BASE_DIR
    target_name = Path(clean).name
    if target_name:
        for match in BASE_DIR.rglob(target_name):
            if match.is_file() and "output" not in match.parts:
                return match.resolve()

    # Fallback to general video search
    fallback = find_video()
    if fallback:
        return fallback

    # If still not found, return the resolved BASE_DIR path for clear error reporting
    return (BASE_DIR / clean).resolve()


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--video",
        required=False,
        default=None,
        help="Optional video path. If omitted, video is found automatically."
    )

    parser.add_argument(
        "--camera-id",
        default="CAM-001"
    )

    parser.add_argument(
        "--location",
        default="Demo Surveillance Zone"
    )

    parser.add_argument(
        "--output",
        default=str(
            BASE_DIR / "output" / "demo_annotated.mp4"
        )
    )

    parser.add_argument(
        "--skip",
        type=int,
        default=2,
        help="Process every Nth frame"
    )

    args = parser.parse_args()


    # ========================================================
    # RESOLVE VIDEO
    # ========================================================

    video = resolve_video_path(args.video)


    print("=" * 70)
    print("SENTINEL AI - DUMMY CCTV TEST")
    print("=" * 70)


    if video is None:

        print()
        print("ERROR: No MP4 video was found inside the project.")
        print()
        print("Project directory:")
        print(BASE_DIR)
        print()
        print("MP4 files found:")

        for p in BASE_DIR.rglob("*.mp4"):
            print(" ", p)

        raise SystemExit(1)


    print()
    print("Video path:")
    print(video)
    print()


    # ========================================================
    # CHECK FILE
    # ========================================================

    if not video.exists():

        print("ERROR: Video file does not exist.")
        print("Checked:")
        print(video)

        raise SystemExit(1)


    if not video.is_file():

        print("ERROR: Selected video path is not a file.")
        print(video)

        raise SystemExit(1)


    # ========================================================
    # RESET AI STATE
    # ========================================================

    reid.reset()
    db.init_db()


    # ========================================================
    # CONFIGURE SENTINEL SERVER
    # ========================================================

    server._cameras = {

        args.camera_id: {

            "id": args.camera_id,

            "location": args.location,

            "source": str(video),

            "status": "RUNNING",

            "frames": 0,

            "fps": 0.0,

            "resolution": "",

            "vehicles_current": 0,

            "anpr_count": 0,

            "ai_confidence": 0.0,

            "last_frame_time": None,
        }
    }


    # ========================================================
    # OPEN VIDEO
    # ========================================================

    video_path_str = os.path.normpath(str(video))
    cap = cv2.VideoCapture(video_path_str)


    if not cap.isOpened():

        print("ERROR: OpenCV could not open the video.")
        print()
        print("Path used:")
        print(video_path_str)
        print()
        print("Trying OpenCV with an alternate backend...")

        cap.release()

        cap = cv2.VideoCapture(
            video_path_str,
            cv2.CAP_FFMPEG
        )


    if not cap.isOpened():

        print()
        print("ERROR: OpenCV cannot decode this video.")
        print()
        print("The file exists, but OpenCV cannot open it.")
        print("Try converting the video to H.264 MP4.")
        print()

        raise SystemExit(1)


    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    fps = cap.get(cv2.CAP_PROP_FPS)

    if not fps or fps <= 0:
        fps = 25.0


    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    total = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )


    if width <= 0:
        width = 1280

    if height <= 0:
        height = 720


    # ========================================================
    # OUTPUT
    # ========================================================

    output_path = Path(args.output)

    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    writer = cv2.VideoWriter(

        str(output_path),

        cv2.VideoWriter_fourcc(
            *"mp4v"
        ),

        fps,

        (width, height)
    )


    if not writer.isOpened():

        cap.release()

        raise SystemExit(
            "Could not create output video."
        )


    # ========================================================
    # START
    # ========================================================

    print("=" * 70)
    print("SENTINEL AI - DUMMY CCTV TEST")
    print("=" * 70)

    print(f"Camera : {args.camera_id}")
    print(f"Video  : {video}")
    print(
        f"Size   : {width}x{height} @ {fps:.1f} FPS"
    )
    print(
        f"Frames : {total}"
    )

    print()
    print("Starting vehicle recognition...")
    print()


    # ========================================================
    # PROCESS VIDEO
    # ========================================================

    detections_log = []

    frame_idx = 0

    processed = 0

    started = time.time()


    while True:

        ok, frame = cap.read()

        if not ok:
            break


        frame_idx += 1


        # Process every Nth frame.
        if frame_idx % max(1, args.skip) == 0:

            processed += 1


            try:

                detections = server.process_ai_frame(
                    args.camera_id,
                    frame,
                    frame_idx
                )

            except Exception as e:

                print(
                    f"[Frame {frame_idx}] "
                    f"AI processing error: {e}"
                )

                detections = []


            try:

                annotated = server.annotate_frame(
                    frame,
                    detections
                )

            except Exception:

                annotated = frame


            # ================================================
            # SAVE DETECTIONS
            # ================================================

            for d in detections:

                detections_log.append(d)


                print(

                    f"[{frame_idx:05d}] "
                    f"{d.get('vehicle_id', 'UNKNOWN')} | "

                    f"{d.get('vehicle_type', 'UNKNOWN')} | "

                    f"{d.get('color', 'UNKNOWN')} | "

                    f"Plate: "
                    f"{d.get('number_plate', 'UNKNOWN')} | "

                    f"Conf: "
                    f"{float(d.get('detection_confidence', 0)):.1f}%"

                )


        else:

            annotated = frame


        writer.write(annotated)


    # ========================================================
    # CLEANUP
    # ========================================================

    cap.release()

    writer.release()


    try:

        reid.flush_to_json()

    except Exception as e:

        print(
            f"Warning: could not flush ReID data: {e}"
        )


    elapsed = time.time() - started


    # ========================================================
    # SUMMARY
    # ========================================================

    unique_ids = sorted(

        {
            d.get(
                "vehicle_id",
                "UNKNOWN"
            )

            for d in detections_log

        }

    )


    plates = sorted(

        {
            d.get(
                "number_plate",
                "UNKNOWN"
            )

            for d in detections_log

            if d.get(
                "number_plate",
                "UNKNOWN"
            ) != "UNKNOWN"

        }

    )


    summary = {

        "camera_id":
            args.camera_id,

        "video":
            str(video),

        "frames_total":
            frame_idx,

        "frames_processed_by_ai":
            processed,

        "detections":
            len(detections_log),

        "unique_vehicle_ids":
            unique_ids,

        "recognized_plates":
            plates,

        "runtime_seconds":
            round(
                elapsed,
                2
            ),

        "output_video":
            str(output_path),
    }


    # ========================================================
    # SAVE JSON
    # ========================================================

    json_path = (
        BASE_DIR
        / "output"
        / "demo_detections.json"
    )


    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            {
                "summary": summary,
                "detections": detections_log
            },

            f,

            indent=2,

            default=str
        )


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    print(
        f"Frames scanned : {frame_idx}"
    )

    print(
        f"AI frames      : {processed}"
    )

    print(
        f"Detections     : {len(detections_log)}"
    )

    print(
        "Vehicle IDs    : "
        + (
            ", ".join(unique_ids)
            if unique_ids
            else "NONE"
        )
    )

    print(
        "Plates         : "
        + (
            ", ".join(plates)
            if plates
            else "NONE READ"
        )
    )

    print(
        f"Annotated video: {output_path}"
    )

    print(
        f"Detection JSON : {json_path}"
    )

    print(
        f"Database       : {db.DATABASE_PATH}"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()