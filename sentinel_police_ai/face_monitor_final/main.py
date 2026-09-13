from camera_manager import (
    get_available_cameras,
    print_camera_catalogue
)
from stream import run_camera_streams


# ============================================================
# START
# ============================================================

print("\nStarting camera discovery...")


# ============================================================
# GET LIVE CAMERA CATALOGUE
# ============================================================

camera_data = get_available_cameras()


# ============================================================
# SHOW RESULT
# ============================================================

print_camera_catalogue(
    camera_data
)

if camera_data:

    run_camera_streams(camera_data)

else:

    print("\nNo cameras available.")