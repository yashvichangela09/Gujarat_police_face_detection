"""
camera_service.py
Background multi-camera vehicle detection service for the Sentinel website.

The Sentinel website runs the cameras. This AI service runs in the
background and provides two integration modes:

  MODE 1 - WEBSITE SENDS FRAMES (recommended for your setup)
      Your website captures frames from its cameras and POSTs them to:
          POST /api/detect
      Body: { "camera_id": "CAM_01", "image": "<base64 JPEG>" }
      Response: detected vehicles with global IDs, plates, colors, routes

  MODE 2 - AI SERVICE CONNECTS TO RTSP
      The AI service connects directly to RTSP streams listed in
      config/multi_camera_config.json and processes them continuously.

  QUERY ENDPOINTS (your website polls these to display data):
      GET /api/vehicles          -> all detected vehicles (JSON)
      GET /api/vehicles/<id>     -> single vehicle detail + route
      GET /api/stats             -> multi-camera re-ID summary
      GET /api/cameras           -> camera statuses
      GET /api/health            -> service health

Run:  python camera_service.py
"""

import os
import sys
import json
import time
import base64
import threading
import numpy as np
import cv2
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from multi_camera_manager import MultiCameraManager
import cross_camera_reid as reid
import pipeline_core as core

DEFAULT_CONFIG = os.path.join(BASE_DIR, "config", "multi_camera_config.json")
HOST = "0.0.0.0"
PORT = 8080
FLUSH_INTERVAL = 5.0   # seconds between registry -> JSON/DB flushes


class CameraService:
    """
    Background AI vehicle detection service.

    Your Sentinel website either:
      A) POSTs camera frames to /api/detect, or
      B) lets this service connect to RTSP streams from the config file.

    Either way, the service detects vehicles, assigns global IDs across
    all cameras, and exposes the data via HTTP API for your website.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG, port: int = PORT):
        self.config_path = config_path
        self.port = port
        self.manager = MultiCameraManager()
        self._stop_evt = threading.Event()
        self._flush_thread = None
        self._httpd = None
        self._http_thread = None
        self.started_cameras = 0
        self.frames_received = 0
        self.detections_made = 0

        # shared models (thread-safe lazy loading)
        self._vehicle_model = None
        self._plate_model = None

    # ── lifecycle ───────────────────────────────────────────────────────────

    def start(self):
        """Start optional RTSP cameras + HTTP API + background flush loop."""
        # 1. optionally start cameras from config (MODE 2)
        if os.path.exists(self.config_path):
            self.started_cameras = self.manager.add_cameras_from_json(
                self.config_path)
            if self.started_cameras:
                print(f"[camera_service] Started {self.started_cameras} "
                      f"RTSP cameras from {self.config_path}")
            else:
                print("[camera_service] No cameras started from config. "
                      "Waiting for frames from website (MODE 1).")
        else:
            print(f"[camera_service] Config not found: {self.config_path}")
            print("[camera_service] Running in MODE 1 - waiting for "
                  "frames from your website.")

        # 2. background flush loop (registry -> JSON + DB)
        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True,
            name="registry-flush")
        self._flush_thread.start()

        # 3. HTTP API server
        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer((HOST, self.port), handler)
        self._http_thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True,
            name="http-api")
        self._http_thread.start()
        print(f"[camera_service] HTTP API running at "
              f"http://{HOST}:{self.port}")
        print("[camera_service] Endpoints:")
        print("  POST /api/detect          <- website sends camera frames")
        print("  GET  /api/vehicles        <- website gets vehicle data")
        print("  GET  /api/vehicles/<id>   <- single vehicle detail")
        print("  GET  /api/stats           <- multi-camera summary")
        print("  GET  /api/cameras         <- camera statuses")
        print("  GET  /api/health          <- service health")

    def stop(self):
        """Stop all cameras, HTTP server, and flush loop."""
        self._stop_evt.set()
        self.manager.stop_all()
        if self._httpd:
            self._httpd.shutdown()
        print("[camera_service] Stopped.")

    # ── background flush ────────────────────────────────────────────────────

    def _flush_loop(self):
        while not self._stop_evt.is_set():
            try:
                reid.flush_to_json()
            except Exception:
                pass
            self._stop_evt.wait(FLUSH_INTERVAL)

    # ── frame processing (MODE 1 - website sends frames) ───────────────────

    def process_frame_from_website(self, camera_id: str, image_bgr) -> list:
        """
        Run the full detection pipeline on a frame sent by the website.

        Returns list of vehicle dicts:
        [{
            "vehicle_id", "vehicle_type", "color", "number_plate",
            "plate_confidence", "detection_confidence", "bounding_box",
            "is_new", "camera_id", "route"
        }]
        """
        self.frames_received += 1

        # lazy-load shared models
        if self._vehicle_model is None:
            self._vehicle_model = core.get_vehicle_model()
        if self._plate_model is None:
            self._plate_model = core.get_plate_model()

        h, w = image_bgr.shape[:2]
        results = self._vehicle_model.predict(
            image_bgr, conf=0.35,
            classes=[2, 3, 5, 7],
            imgsz=640, verbose=False)

        detections = []

        for box in (results[0].boxes or []):
            class_id   = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(w, x2); y2 = min(h, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            crop = image_bgr[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            from vehicle_attributes import get_vehicle_color, get_vehicle_type
            vtype = get_vehicle_type(class_id, crop)
            color = get_vehicle_color(crop)

            # plate detection
            plate_text, plate_conf = "UNKNOWN", 0.0
            if self._plate_model is not None:
                try:
                    pr = self._plate_model(crop, verbose=False)
                    for pres in pr:
                        for pbox in (pres.boxes or []):
                            px1, py1, px2, py2 = \
                                pbox.xyxy[0].cpu().numpy().astype(int)
                            pad = 8
                            ph, pw = crop.shape[:2]
                            px1 = max(0, px1 - pad); py1 = max(0, py1 - pad)
                            px2 = min(pw, px2 + pad); py2 = min(ph, py2 + pad)
                            pcrop = crop[py1:py2, px1:px2]
                            if pcrop.size > 0:
                                plate_text, plate_conf = core._ocr_plate(pcrop)
                except Exception:
                    pass

            # cross-camera global ID assignment
            global_id, is_new = reid.match_or_register(
                vehicle_type=vtype,
                color=color,
                number_plate=plate_text,
                plate_conf=plate_conf,
                crop=crop,
                camera_id=str(camera_id),
                frame_number=self.frames_received,
            )

            # save crop
            crop_dir = os.path.join(BASE_DIR, "output", "vehicle_crops")
            os.makedirs(crop_dir, exist_ok=True)
            crop_path = os.path.join(crop_dir, f"{global_id}.jpg")
            if not os.path.exists(crop_path):
                cv2.imwrite(crop_path, crop)

            self.detections_made += 1

            detections.append({
                "vehicle_id":           global_id,
                "vehicle_type":         vtype,
                "color":                color,
                "number_plate":         plate_text,
                "plate_confidence":     plate_conf,
                "detection_confidence": round(confidence * 100, 2),
                "bounding_box":         {"x1": int(x1), "y1": int(y1),
                                         "x2": int(x2), "y2": int(y2)},
                "is_new":               is_new,
                "camera_id":            str(camera_id),
                "route":                reid.get_vehicle_route(global_id),
            })

        return detections

    # ── HTTP API ────────────────────────────────────────────────────────────

    def _make_handler(self):
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass   # silence default request logging

            def _send_json(self, obj, status=200):
                body = json.dumps(obj, indent=2, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods",
                                 "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers",
                                 "Content-Type")
                self.end_headers()

            def do_POST(self):
                path = self.path.split("?")[0].rstrip("/")

                if path == "/api/detect":
                    # website sends a camera frame for detection
                    try:
                        length = int(self.headers.get("Content-Length", 0))
                        raw = self.rfile.read(length)
                        data = json.loads(raw.decode("utf-8"))

                        camera_id = data.get("camera_id", "WEBSITE_CAM")
                        img_b64 = data.get("image", "")
                        if not img_b64:
                            self._send_json(
                                {"error": "Missing 'image' (base64 JPEG)"},
                                status=400)
                            return

                        # decode base64 -> numpy BGR
                        img_bytes = base64.b64decode(img_b64)
                        img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
                        frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                        if frame is None:
                            self._send_json(
                                {"error": "Invalid image data"},
                                status=400)
                            return

                        detections = service.process_frame_from_website(
                            camera_id, frame)

                        self._send_json({
                            "camera_id":   str(camera_id),
                            "detections":  detections,
                            "count":       len(detections),
                            "total_vehicles": service.manager.total_vehicles(),
                            "time":        time.strftime("%Y-%m-%dT%H:%M:%S"),
                        })
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=500)

                else:
                    self._send_json({"error": "Not found"}, status=404)

            def do_GET(self):
                path = self.path.split("?")[0].rstrip("/")

                if path == "/api/health":
                    self._send_json({
                        "status": "online",
                        "mode": "website-frames" if not service.started_cameras
                                else "rtsp+website-frames",
                        "cameras_started": service.started_cameras,
                        "cameras_active": service.manager.active_count(),
                        "frames_received": service.frames_received,
                        "detections_made": service.detections_made,
                        "vehicles": service.manager.total_vehicles(),
                        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    })

                elif path == "/api/vehicles":
                    self._send_json(service.manager.get_all_vehicles())

                elif path.startswith("/api/vehicles/"):
                    vid = path.split("/")[-1]
                    veh = reid.get_vehicle(vid)
                    if veh is None:
                        self._send_json({"error": f"Vehicle {vid} not found"},
                                        status=404)
                    else:
                        veh["route"] = reid.get_vehicle_route(vid)
                        self._send_json(veh)

                elif path == "/api/stats":
                    self._send_json(service.manager.multi_camera_summary())

                elif path == "/api/cameras":
                    self._send_json(service.manager.camera_statuses())

                else:
                    self._send_json({
                        "error": "Not found",
                        "endpoints": [
                            "POST /api/detect",
                            "GET  /api/health",
                            "GET  /api/vehicles",
                            "GET  /api/vehicles/<id>",
                            "GET  /api/stats",
                            "GET  /api/cameras",
                        ],
                    }, status=404)

        return Handler


# ── run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Background AI vehicle detection service for Sentinel website")
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="Path to camera config JSON (optional)")
    parser.add_argument("--port", type=int, default=PORT,
                        help="HTTP API port (default 8080)")
    args = parser.parse_args()

    service = CameraService(config_path=args.config, port=args.port)
    service.start()

    print("\n[camera_service] Running in background. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
        print("[camera_service] Exited.")