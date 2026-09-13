import requests

from config import INGEST_API


# ============================================================
# FETCH CAMERA CATALOGUE/ USING DUMMY VIDEO WITH RTSP LINK
# ============================================================

USE_DUMMY_CAMERA = True


DUMMY_CAMERA = [{
    "id": "dummy1",
    "location": "Dummy Test Camera",
    "codec": "h264",
    "live": True,

    # RTSP feed created by FFmpeg + MediaMTX
    "rtsp_url": "rtsp://127.0.0.1:8554/stream/dummy1"
},
{
    "id": "dummy2",
    "location": "Dummy Test Camera",
    "codec": "h264",
    "live": True,

    # RTSP feed created by FFmpeg + MediaMTX
    "rtsp_url": "rtsp://127.0.0.1:8554/stream/dummy1"
},
{
    "id": "dummy3",
    "location": "Dummy Test Camera",
    "codec": "h264",
    "live": True,

    # RTSP feed created by FFmpeg + MediaMTX
    "rtsp_url": "rtsp://127.0.0.1:8554/stream/dummy1"
},
{
    "id": "dummy4",
    "location": "Dummy Test Camera",
    "codec": "h264",
    "live": True,

    # RTSP feed created by FFmpeg + MediaMTX
    "rtsp_url": "rtsp://127.0.0.1:8554/stream/dummy1"
}]

def get_available_cameras():


    if USE_DUMMY_CAMERA:
        return DUMMY_CAMERA


    try:

        response = requests.get(
            INGEST_API,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as error:

        print(
            f"\nCamera catalogue error:\n"
            f"{error}"
        )

        return None

    except ValueError:

        print(
            "\n/api/ingest did not return valid JSON."
        )

        return None


# ============================================================
# DISPLAY RAW CATALOGUE
# ============================================================

def print_camera_catalogue(data):

    if data is None:

        print(
            "No camera catalogue available."
        )

        return


    print("\n" + "=" * 70)

    print("CAMERA CATALOGUE")

    print("=" * 70)

    for camera in data:

        print(f"ID       : {camera.get('id')}")
        print(f"Location : {camera.get('location')}")
        print(f"Codec    : {camera.get('codec')}")
        print(f"Live     : {camera.get('live')}")
        print(f"RTSP     : {camera.get('rtsp_url')}")

        print("-" * 70)