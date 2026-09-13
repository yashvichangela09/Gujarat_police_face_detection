"""
main.py
Master orchestrator for the SENTINEL AI Multi-Camera Vehicle Intelligence System.

Single-command execution:
    python main.py
    (or python app.py)

Performs:
  1. System and dependency verification
  2. Model pre-check and database initialization
  3. Spawning 3 concurrent camera AI workers (CAMERA_01, CAMERA_02, CAMERA_03)
  4. Launching Flask + Socket.IO real-time web server
  5. Automatically opening the browser dashboard at http://127.0.0.1:5000
"""

import os
import sys

# Safe UTF-8 configuration on Windows cmd/powershell without detaching buffers
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Critical Windows Python 3.12 DLL order & oneDNN CPU fix
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
try:
    import torch
    torch.set_num_threads(2)
except Exception:
    pass

import cv2
cv2.setNumThreads(2)


import time
import threading
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import sentinel_db as db
import pipeline_core as core
import sentinel_server


def print_banner():
    banner = """
==============================================================================
   SENTINEL AI - MULTI-CAMERA VEHICLE INTELLIGENCE COMMAND CENTER
   Real-Time CCTV Tracking | License Plate OCR | Cross-Camera Re-ID
==============================================================================
"""
    print(banner)


def check_and_initialize():
    print("[1/4] Checking database and directory structure...")
    db.init_db()
    for d in ["output", "output/plate_crops", "output/vehicle_crops"]:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
    print(f"      SQLite DB Ready: {db.DATABASE_PATH}")

    print("[2/4] Verifying AI models...")
    v_model = core.get_vehicle_model()
    if v_model is not None:
        print("      [OK] YOLO Vehicle Detector loaded successfully")
    else:
        print("      [WARN] YOLO Vehicle Detector could not be loaded")

    p_model = core.get_plate_model()
    if p_model is not None:
        print("      [OK] License Plate Detector loaded successfully")
    else:
        print("      [WARN] License Plate Detector could not be loaded")

    print("[3/4] Initializing CCTV camera surveillance nodes...")
    sentinel_server.init_cameras()
    print(f"      Configured {len(sentinel_server._cameras)} active camera nodes:")
    for cid, cam in sentinel_server._cameras.items():
        src_disp = os.path.basename(cam['source']) if cam['source'] else 'None'
        print(f"        * {cid} [{cam['location']}] -> Source: {src_disp}")

    print("[4/4] Starting concurrent camera AI pipeline threads...")
    sentinel_server.start_all_cameras()
    print("      [OK] Camera worker threads operational with frame staggering.")


def auto_open_browser(port=5000):
    """Wait for server to bind, then open the default browser."""
    time.sleep(2.0)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[SENTINEL] Opening Command Center in browser: {url}\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[SENTINEL] Browser auto-open failed: {e}. Please navigate to {url} manually.")


def main():
    print_banner()
    check_and_initialize()

    port = 5000
    # Launch browser thread
    threading.Thread(target=auto_open_browser, args=(port,), daemon=True).start()

    print("-" * 78)
    print(f"  COMMAND CENTER WEB DASHBOARD:  http://127.0.0.1:{port}")
    print(f"  CAMERA STREAMS:                http://127.0.0.1:{port}/api/camera/<id>/stream")
    print("  Press Ctrl+C to terminate the system.")
    print("-" * 78 + "\n")

    try:
        sentinel_server.socketio.run(
            sentinel_server.app,
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True,
        )
    except KeyboardInterrupt:
        print("\n[SENTINEL] Gracefully stopping camera workers...")
        sentinel_server.stop_all_cameras()
        print("[SENTINEL] System shutdown complete.")


if __name__ == "__main__":
    main()