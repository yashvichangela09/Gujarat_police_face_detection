# ============================================================
# REVISION 18 — MULTI-CAMERA LIVE STREAM + FACE RECOGNITION
#
# Features:
#   - Multiple RTSP cameras simultaneously
#   - One worker thread per camera
#   - Latest-frame buffer
#   - Dynamic camera grid
#   - InsightFace recognition
#   - 35% possible threshold
#   - 40% identified threshold
#   - Confirmation before alert
#   - Automatic reconnect
#   - CPU-friendly recognition
#   - Only camera title + face recognition overlay
# ============================================================


import os
import time
import threading
import math

import cv2
import numpy as np

from insightface.app import FaceAnalysis


# ============================================================
# REVISION 18.1 — FORCE RTSP OVER TCP
# ============================================================

os.environ[
    "OPENCV_FFMPEG_CAPTURE_OPTIONS"
] = "rtsp_transport;tcp"


# ============================================================
# CONFIG IMPORT
# ============================================================

from config import (
    INITIAL_RECONNECT_DELAY,
    MAX_RECONNECT_DELAY,
    RECONNECT_BACKOFF_MULTIPLIER,
    MAX_CONSECUTIVE_READ_FAILURES,
    SHOW_VIDEO,
    DISPLAY_WIDTH,
    CAPTURE_BUFFER_SIZE
)


# ============================================================
# FACE RECOGNITION SETTINGS
# ============================================================

POSSIBLE_THRESHOLD = 0.20

IDENTIFIED_THRESHOLD = 0.35

PROCESS_EVERY_N_FRAMES = 5

CONFIRMATION_FRAMES = 2

ALERT_COOLDOWN_SECONDS = 30

DISAPPEARANCE_SECONDS = 5


# ============================================================
# GRID SETTINGS
# ============================================================

GRID_WINDOW_NAME = "All Cameras"

GRID_WIDTH = 1280

GRID_HEIGHT = 720

GRID_BACKGROUND = (20, 20, 20)

GRID_GAP = 2


# ============================================================
# KNOWN FACES DIRECTORY
# ============================================================

KNOWN_FACES_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "known_faces"
)


# ============================================================
# INSIGHTFACE MODEL
# ============================================================

print("\nLoading InsightFace model...")

app = FaceAnalysis(
    name="buffalo_s",
    providers=[
        "CPUExecutionProvider"
    ]
)

app.prepare(
    ctx_id=-1,
    det_size=(320, 320)
)

print("InsightFace model loaded.")


# ============================================================
# GLOBAL KNOWN FACE DATA
# ============================================================

known_faces = {}


# ============================================================
# MULTI-CAMERA SHARED DATA
# ============================================================

latest_frames = {}

frame_locks = {}

camera_status = {}

camera_status_locks = {}

stop_event = threading.Event()

worker_threads = []


# ============================================================
# RECOGNITION TRACKING
#
# Separate tracking state for every camera.
# ============================================================

person_tracks = {}

person_tracks_lock = threading.Lock()


# ============================================================
# LOAD KNOWN FACES
# ============================================================

def load_known_faces():

    global known_faces

    known_faces = {}

    if not os.path.isdir(
        KNOWN_FACES_DIR
    ):

        print(
            f"\nKnown faces directory not found:"
            f"\n{KNOWN_FACES_DIR}"
        )

        return


    print("\nLoading known faces...")


    for person_name in os.listdir(
        KNOWN_FACES_DIR
    ):

        person_folder = os.path.join(
            KNOWN_FACES_DIR,
            person_name
        )


        if not os.path.isdir(
            person_folder
        ):
            continue


        embeddings = []


        for filename in os.listdir(
            person_folder
        ):

            image_path = os.path.join(
                person_folder,
                filename
            )


            image = cv2.imread(
                image_path
            )


            if image is None:

                print(
                    f"Could not read:"
                    f" {image_path}"
                )

                continue


            faces = app.get(
                image
            )


            if not faces:

                print(
                    f"No face found in:"
                    f" {filename}"
                )

                continue


            # ------------------------------------------------
            # If multiple faces exist, use the largest face.
            # ------------------------------------------------

            face = max(
                faces,
                key=lambda f:
                (
                    f.bbox[2] - f.bbox[0]
                )
                *
                (
                    f.bbox[3] - f.bbox[1]
                )
            )


            embedding = np.asarray(
                face.embedding,
                dtype=np.float32
            )


            norm = np.linalg.norm(
                embedding
            )


            if norm == 0:
                continue


            embedding = (
                embedding / norm
            )


            embeddings.append(
                embedding
            )


        if embeddings:

            known_faces[
                person_name
            ] = embeddings


            print(
                f"Loaded {person_name}: "
                f"{len(embeddings)} reference(s)"
            )


    print(
        f"\nTotal known people: "
        f"{len(known_faces)}"
    )


# ============================================================
# FIND BEST FACE MATCH
# ============================================================

def find_best_match(
    face
):

    if not known_faces:

        return None, 0.0


    live_embedding = np.asarray(
        face.embedding,
        dtype=np.float32
    )


    norm = np.linalg.norm(
        live_embedding
    )


    if norm == 0:

        return None, 0.0


    live_embedding = (
        live_embedding / norm
    )


    best_person = None

    best_score = 0.0


    # --------------------------------------------------------
    # Compare against EVERY reference embedding.
    #
    # We intentionally do NOT average them.
    # --------------------------------------------------------

    for person_name, references in (
        known_faces.items()
    ):

        for reference_embedding in references:

            score = float(
                np.dot(
                    live_embedding,
                    reference_embedding
                )
            )


            if score > best_score:

                best_score = score

                best_person = (
                    person_name
                )


    # --------------------------------------------------------
    # Ignore low-confidence faces completely.
    # --------------------------------------------------------

    if best_score < POSSIBLE_THRESHOLD:

        return None, 0.0


    return (
        best_person,
        best_score
    )


# ============================================================
# ALERT
# ============================================================

def send_alert(
    camera_id,
    person_name,
    score
):

    print(
        "\n"
        + "!" * 60
    )

    print(
        f"ALERT: {person_name} "
        f"found in Camera {camera_id}"
    )

    print(
        f"Match chance: "
        f"{score * 100:.1f}%"
    )

    print(
        "!" * 60
        + "\n"
    )


# ============================================================
# UPDATE PERSON TRACK
# ============================================================

def update_person_track(
    camera_id,
    person_name,
    score
):

    now = time.monotonic()


    key = (
        camera_id,
        person_name
    )


    with person_tracks_lock:

        if key not in person_tracks:

            person_tracks[key] = {

                "state": "POSSIBLE",

                "best_score": score,

                "last_score": score,

                "last_seen": now,

                "confirmation_count": 0,

                "last_alert": 0
            }


        track = person_tracks[key]


        track[
            "last_seen"
        ] = now


        track[
            "last_score"
        ] = score


        if score > track[
            "best_score"
        ]:

            track[
                "best_score"
            ] = score


        # ----------------------------------------------------
        # IDENTIFICATION CONFIRMATION
        # ----------------------------------------------------

        if score >= IDENTIFIED_THRESHOLD:

            track[
                "confirmation_count"
            ] += 1


            if (
                track["confirmation_count"]
                >= CONFIRMATION_FRAMES
            ):

                track[
                    "state"
                ] = "IDENTIFIED"


                # --------------------------------------------
                # ALERT COOLDOWN
                # --------------------------------------------

                if (
                    now
                    -
                    track["last_alert"]
                    >= ALERT_COOLDOWN_SECONDS
                ):

                    send_alert(
                        camera_id,
                        person_name,
                        score
                    )


                    track[
                        "last_alert"
                    ] = now


        else:

            track[
                "state"
            ] = "POSSIBLE"


        return (
            track["state"],
            track["last_score"]
        )


# ============================================================
# REMOVE DISAPPEARED PEOPLE
# ============================================================

def remove_disappeared_people(
    camera_id
):

    now = time.monotonic()


    with person_tracks_lock:

        keys_to_remove = []


        for key, track in (
            person_tracks.items()
        ):

            key_camera_id, person_name = key


            if key_camera_id != camera_id:

                continue


            if (
                now
                -
                track["last_seen"]
                >
                DISAPPEARANCE_SECONDS
            ):

                keys_to_remove.append(
                    key
                )


        for key in keys_to_remove:

            person_tracks.pop(
                key,
                None
            )


# ============================================================
# DRAW RECOGNITION RESULT
# ============================================================

def draw_recognition_result(
    frame,
    bbox,
    person_name,
    score
):

    x1, y1, x2, y2 = map(
        int,
        bbox
    )


    if score >= IDENTIFIED_THRESHOLD:

        label = (
            f"IDENTIFIED | "
            f"{person_name} | "
            f"{score * 100:.1f}%"
        )

    else:

        label = (
            f"POSSIBLE | "
            f"{person_name} | "
            f"{score * 100:.1f}%"
        )


    # --------------------------------------------------------
    # Bounding box
    # --------------------------------------------------------

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )


    # --------------------------------------------------------
    # Label background
    # --------------------------------------------------------

    font_scale = 0.4

    font_thickness = 1


    (
        text_width,
        text_height
    ), baseline = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        font_thickness
    )


    label_y = max(
        y1 - 10,
        text_height + 10
    )


    cv2.rectangle(
        frame,
        (
            x1,
            label_y
            - text_height
            - baseline
            - 5
        ),
        (
            x1
            + text_width
            + 5,
            label_y + 5
        ),
        (0, 0, 0),
        -1
    )


    # --------------------------------------------------------
    # Text
    # --------------------------------------------------------

    cv2.putText(
        frame,
        label,
        (
            x1,
            label_y
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 255, 0),
        font_thickness
    )


# ============================================================
# PROCESS ONE CAMERA FRAME
# ============================================================

def process_camera_frame(
    camera_id,
    frame,
    frame_count,
    last_recognition_results
):

    # --------------------------------------------------------
    # Run recognition only every N frames.
    # --------------------------------------------------------

    if (
        frame_count
        %
        PROCESS_EVERY_N_FRAMES
        == 0
    ):

        faces = app.get(
            frame
        )


        recognition_results = []


        for face in faces:

            person_name, score = (
                find_best_match(face)
            )


            # ------------------------------------------------
            # Unknown / low score:
            #
            # Do absolutely nothing.
            # ------------------------------------------------

            if person_name is None:

                continue


            state, current_score = (
                update_person_track(
                    camera_id,
                    person_name,
                    score
                )
            )


            recognition_results.append(
                {
                    "bbox": face.bbox.copy(),

                    "person_name":
                        person_name,

                    "score":
                        current_score,

                    "state":
                        state
                }
            )


        last_recognition_results = (
            recognition_results
        )


    # --------------------------------------------------------
    # Remove people that disappeared.
    # --------------------------------------------------------

    remove_disappeared_people(
        camera_id
    )


    # --------------------------------------------------------
    # Draw only relevant faces.
    # --------------------------------------------------------

    for result in (
        last_recognition_results
    ):

        draw_recognition_result(
            frame,
            result["bbox"],
            result["person_name"],
            result["score"]
        )


    return last_recognition_results


# ============================================================
# UPDATE SHARED FRAME
# ============================================================

def update_latest_frame(
    camera_id,
    frame
):

    lock = frame_locks[
        camera_id
    ]


    with lock:

        # ----------------------------------------------------
        # Store only the latest frame.
        #
        # Old frames are discarded.
        # ----------------------------------------------------

        latest_frames[
            camera_id
        ] = frame


# ============================================================
# CAMERA WORKER
# ============================================================

def camera_worker(
    camera
):

    camera_id = camera.get(
        "id",
        "unknown"
    )


    rtsp_url = camera.get(
        "rtsp_url"
    )


    if not rtsp_url:

        print(
            f"No RTSP URL for "
            f"Camera {camera_id}"
        )

        return


    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Starting Camera {camera_id}"
    )

    print(
        f"RTSP: {rtsp_url}"
    )

    print(
        "=" * 70
    )


    reconnect_delay = (
        INITIAL_RECONNECT_DELAY
    )


    frame_count = 0

    last_recognition_results = []


    while not stop_event.is_set():

        print(
            f"\nConnecting to "
            f"Camera {camera_id}..."
        )


        capture = cv2.VideoCapture(
            rtsp_url,
            cv2.CAP_FFMPEG
        )


        capture.set(
            cv2.CAP_PROP_BUFFERSIZE,
            CAPTURE_BUFFER_SIZE
        )


        if not capture.isOpened():

            print(
                f"Could not connect to "
                f"Camera {camera_id}"
            )


            capture.release()


            print(
                f"Retrying Camera "
                f"{camera_id} in "
                f"{reconnect_delay} seconds..."
            )


            stop_event.wait(
                reconnect_delay
            )


            reconnect_delay = min(
                reconnect_delay
                *
                RECONNECT_BACKOFF_MULTIPLIER,
                MAX_RECONNECT_DELAY
            )


            continue


        print(
            f"Connected to "
            f"Camera {camera_id}"
        )


        reconnect_delay = (
            INITIAL_RECONNECT_DELAY
        )


        consecutive_failures = 0


        # ====================================================
        # FRAME LOOP
        # ====================================================

        while not stop_event.is_set():

            success, frame = (
                capture.read()
            )


            # ------------------------------------------------
            # READ FAILURE
            # ------------------------------------------------

            if not success:

                consecutive_failures += 1


                if (
                    consecutive_failures
                    <
                    MAX_CONSECUTIVE_READ_FAILURES
                ):

                    time.sleep(
                        0.1
                    )

                    continue


                print(
                    f"\nCamera {camera_id} "
                    f"stream interrupted."
                )


                break


            consecutive_failures = 0

            frame_count += 1


            # ------------------------------------------------
            # FACE RECOGNITION
            # ------------------------------------------------

            process_camera_frame(
                camera_id,
                frame,
                frame_count,
                last_recognition_results
            )


            # ------------------------------------------------
            # CAMERA TITLE
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Camera: {camera_id}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )


            # ------------------------------------------------
            # SAVE LATEST FRAME
            # ------------------------------------------------

            update_latest_frame(
                camera_id,
                frame
            )


        capture.release()


        if stop_event.is_set():

            break


        print(
            f"Camera {camera_id} "
            f"capture released."
        )


        print(
            f"Reconnecting Camera "
            f"{camera_id} in "
            f"{reconnect_delay} seconds..."
        )


        stop_event.wait(
            reconnect_delay
        )


        reconnect_delay = min(
            reconnect_delay
            *
            RECONNECT_BACKOFF_MULTIPLIER,
            MAX_RECONNECT_DELAY
        )


    print(
        f"Camera {camera_id} worker stopped."
    )


# ============================================================
# CREATE GRID
# ============================================================

def create_camera_grid(
    cameras
):

    camera_count = len(
        cameras
    )


    if camera_count == 0:

        return np.zeros(
            (
                GRID_HEIGHT,
                GRID_WIDTH,
                3
            ),
            dtype=np.uint8
        )


    # --------------------------------------------------------
    # Determine grid dimensions.
    #
    # Examples:
    #
    # 1 → 1 x 1
    # 2 → 1 x 2
    # 3 → 2 x 2
    # 4 → 2 x 2
    # 5 → 2 x 3
    # 6 → 2 x 3
    # 7 → 3 x 3
    # 8 → 3 x 3
    # 9 → 3 x 3
    # 10 → 3 x 4
    # --------------------------------------------------------

    columns = math.ceil(
        math.sqrt(camera_count)
    )

    rows = math.ceil(
        camera_count
        /
        columns
    )


    cell_width = (
        GRID_WIDTH
        -
        (columns - 1)
        *
        GRID_GAP
    ) // columns


    cell_height = (
        GRID_HEIGHT
        -
        (rows - 1)
        *
        GRID_GAP
    ) // rows


    grid = np.full(
        (
            GRID_HEIGHT,
            GRID_WIDTH,
            3
        ),
        GRID_BACKGROUND,
        dtype=np.uint8
    )


    # ========================================================
    # PUT EACH CAMERA INTO GRID
    # ========================================================

    for index, camera in enumerate(
        cameras
    ):

        camera_id = camera.get(
            "id",
            "unknown"
        )


        row = (
            index
            //
            columns
        )


        column = (
            index
            %
            columns
        )


        x = (
            column
            *
            (
                cell_width
                +
                GRID_GAP
            )
        )


        y = (
            row
            *
            (
                cell_height
                +
                GRID_GAP
            )
        )


        # ----------------------------------------------------
        # Get latest frame.
        # ----------------------------------------------------

        frame = None


        if camera_id in frame_locks:

            with frame_locks[
                camera_id
            ]:

                if camera_id in latest_frames:

                    frame = (
                        latest_frames[
                            camera_id
                        ].copy()
                    )


        # ----------------------------------------------------
        # No frame yet.
        # ----------------------------------------------------

        if frame is None:

            cell = np.full(
                (
                    cell_height,
                    cell_width,
                    3
                ),
                GRID_BACKGROUND,
                dtype=np.uint8
            )


            cv2.putText(
                cell,
                f"Camera {camera_id}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                1
            )


            cv2.putText(
                cell,
                "Connecting...",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )


        else:

            # ------------------------------------------------
            # Maintain aspect ratio.
            # ------------------------------------------------

            frame_height, frame_width = (
                frame.shape[:2]
            )


            scale = min(
                cell_width
                /
                frame_width,

                cell_height
                /
                frame_height
            )


            new_width = max(
                1,
                int(
                    frame_width
                    *
                    scale
                )
            )


            new_height = max(
                1,
                int(
                    frame_height
                    *
                    scale
                )
            )


            resized = cv2.resize(
                frame,
                (
                    new_width,
                    new_height
                )
            )


            cell = np.full(
                (
                    cell_height,
                    cell_width,
                    3
                ),
                GRID_BACKGROUND,
                dtype=np.uint8
            )


            offset_x = (
                cell_width
                -
                new_width
            ) // 2


            offset_y = (
                cell_height
                -
                new_height
            ) // 2


            cell[
                offset_y:
                offset_y + new_height,

                offset_x:
                offset_x + new_width
            ] = resized


        # ----------------------------------------------------
        # Put cell into grid.
        # ----------------------------------------------------

        grid[
            y:
            y + cell_height,

            x:
            x + cell_width
        ] = cell


    return grid


# ============================================================
# START ALL CAMERAS
# ============================================================

def run_camera_streams(
    cameras
):

    global worker_threads


    if not cameras:

        print(
            "\nNo cameras available."
        )

        return


    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Starting "
        f"{len(cameras)} camera(s)"
    )

    print(
        "=" * 70
    )


    # ========================================================
    # CREATE SHARED STORAGE
    # ========================================================

    for camera in cameras:

        camera_id = camera.get(
            "id",
            "unknown"
        )


        frame_locks[
            camera_id
        ] = threading.Lock()


        camera_status_locks[
            camera_id
        ] = threading.Lock()


        camera_status[
            camera_id
        ] = "STARTING"


    # ========================================================
    # START ONE THREAD PER CAMERA
    # ========================================================

    for camera in cameras:

        thread = threading.Thread(
            target=camera_worker,
            args=(camera,),
            daemon=False
        )


        worker_threads.append(
            thread
        )


        thread.start()


    # ========================================================
    # GRID WINDOW
    # ========================================================

    if SHOW_VIDEO:

        cv2.namedWindow(
            GRID_WINDOW_NAME,
            cv2.WINDOW_NORMAL
        )


        cv2.resizeWindow(
            GRID_WINDOW_NAME,
            GRID_WIDTH,
            GRID_HEIGHT
        )


    try:

        # ====================================================
        # MAIN DISPLAY LOOP
        # ====================================================

        while True:

            if SHOW_VIDEO:

                grid = (
                    create_camera_grid(
                        cameras
                    )
                )


                cv2.imshow(
                    GRID_WINDOW_NAME,
                    grid
                )


                key = (
                    cv2.waitKey(1)
                    &
                    0xFF
                )


                # --------------------------------------------
                # Q = quit
                # --------------------------------------------

                if key == ord("q"):

                    print(
                        "\nStopping all cameras..."
                    )

                    break


    except KeyboardInterrupt:

        print(
            "\nKeyboard interrupt received."
        )


    finally:

        # ====================================================
        # STOP ALL WORKERS
        # ====================================================

        stop_event.set()


        print(
            "\nWaiting for camera workers..."
        )


        for thread in worker_threads:

            thread.join(
                timeout=5
            )


        worker_threads.clear()


        cv2.destroyAllWindows()


        print(
            "All cameras stopped."
        )

# ============================================================
# LOAD KNOWN FACES
# ============================================================

load_known_faces()