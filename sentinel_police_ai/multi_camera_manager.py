"""
multi_camera_manager.py
Manages multiple CCTV cameras simultaneously.
Each camera runs in its own thread.
All detections feed into the cross-camera global registry.

Designed for 20–30 cameras:
  • one daemon thread per camera
  • shared lazy-loaded models via pipeline_core (thread-safe loader)
  • per-camera crop archive (global_id + camera_id in filename)
  • atomic best-crop writes (temp + os.replace) — safe when multiple
    cameras write the same global vehicle's best-crop concurrently
  • reconnect-with-backoff for RTSP / webcam sources
  • batch add helper:  add_cameras_batch([... up to 30 sources ...])
"""

import cv2
import threading
import queue
import time
import os
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import pipeline_core    as core
import cross_camera_reid as reid

# ── shared helpers ────────────────────────────────────────────────────────────

def _atomic_imwrite(path, img):
    """Write image atomically (temp file + os.replace)."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            prefix=".tmp_crop_", suffix=".jpg",
            dir=os.path.dirname(path))
        os.close(fd)
        ok = cv2.imwrite(tmp, img)
        if ok:
            os.replace(tmp, path)
        else:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        return ok
    except Exception:
        return False


# ── per-camera worker ─────────────────────────────────────────────────────────

class CameraWorker:
    """One thread per camera."""

    SLOW_FAST = False   # plate detect cadence handled in worker

    def __init__(self, camera_id, source, event_queue: queue.Queue,
                 frame_skip=3, reconnect: bool = True):
        self.camera_id   = str(camera_id)
        self.source      = source
        self.event_queue = event_queue
        self.frame_skip  = frame_skip
        self.reconnect   = reconnect

        self._stop       = threading.Event()
        self._thread     = None
        self.frame_count = 0
        self.status      = "IDLE"     # IDLE / RUNNING / ERROR / STOPPED
        self.error_msg   = ""
        self.last_error  = None

        self._retry_delay  = 2.0
        self._max_retries  = None      # None = retry forever (RTSP)
        self._plate_cadence = 8        # run plate model every Nth processed frame

        self.crop_dir = os.path.join(BASE_DIR, "output", "vehicle_crops")
        os.makedirs(self.crop_dir, exist_ok=True)

    # ── lifecycle ───────────────────────────────────────────────────────────

    def start(self):
        self._stop.clear()
        self.status  = "RUNNING"
        self._thread = threading.Thread(
            target=self._run, daemon=True,
            name=f"cam-{self.camera_id}")
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.status = "STOPPED"

    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()

    def _emit(self, event: dict):
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            try:
                # never block a camera thread — drop oldest
                self.event_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.event_queue.put_nowait(event)
            except queue.Full:
                pass

    # ── main loop ─────────────────────────────────────────────────────────────

    def _run(self):
        is_file = isinstance(self.source, str) and os.path.isfile(self.source)
        attempts = 0
        cap = None

        # model handles shared across all cameras
        model       = None
        plate_model = None

        try:
            while not self._stop.is_set():
                # ── (re)open source with backoff ─────────────────────────
                cap = cv2.VideoCapture(self.source)
                if not cap.isOpened():
                    if cap is not None:
                        cap.release()
                    cap = None
                    attempts += 1
                    self.status = "ERROR"
                    self.error_msg = f"Cannot open source: {self.source}"
                    self._emit({
                        "type":      "error",
                        "camera_id": self.camera_id,
                        "msg":       self.error_msg,
                    })
                    if self._max_retries is not None and \
                            attempts >= self._max_retries:
                        break
                    time.sleep(min(self._retry_delay * (1 + attempts * 0.5),
                                   30.0))
                    continue

                attempts = 0
                self.error_msg = ""
                self.status = "RUNNING"
                self._emit({
                    "type":      "camera_online",
                    "camera_id": self.camera_id,
                    "source":    str(self.source),
                })

                # lazy-load models ONCE per worker
                if model is None:
                    model = core.get_vehicle_model()
                if plate_model is None:
                    plate_model = core.get_plate_model()

                frame_idx = 0

                try:
                    while not self._stop.is_set():
                        ret, frame = cap.read()
                        if not ret:
                            if is_file:
                                break       # video file ended
                            # camera hiccup — brief pause, then reconnect
                            time.sleep(0.1)
                            break

                        frame_idx        += 1
                        self.frame_count += 1

                        if frame_idx % self.frame_skip != 0:
                            continue

                        h, w = frame.shape[:2]
                        results = model.predict(
                            frame, conf=0.35,
                            classes=[2, 3, 5, 7],
                            imgsz=640, verbose=False)

                        # drain re-id merge notifications
                        for me in reid.take_merge_events():
                            self._emit({
                                "type":        "merge",
                                "vehicle_id":  me.get("vehicle_id"),
                                "merged_from": me.get("merged_from"),
                                "cameras":     me.get("cameras", []),
                                "time":        me.get("time", ""),
                            })

                        for box in (results[0].boxes or []):
                            class_id   = int(box.cls[0].item())
                            confidence = float(box.conf[0].item())
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            x1=max(0,x1); y1=max(0,y1)
                            x2=min(w,x2); y2=min(h,y2)
                            if x2<=x1 or y2<=y1: continue

                            crop  = frame[y1:y2, x1:x2]
                            if crop.size == 0: continue

                            from vehicle_attributes import (
                                get_vehicle_color, get_vehicle_type)
                            vtype = get_vehicle_type(class_id, crop)
                            color = get_vehicle_color(crop)

                            # plate detection (periodic per processed frame)
                            plate_text, plate_conf = "UNKNOWN", 0.0
                            if frame_idx % self._plate_cadence == 0 \
                                    and plate_model is not None:
                                try:
                                    pr = plate_model(crop, verbose=False)
                                    for pres in pr:
                                        for pbox in (pres.boxes or []):
                                            px1,py1,px2,py2 = \
                                                pbox.xyxy[0].cpu().numpy().astype(int)
                                            pad=8; ph,pw=crop.shape[:2]
                                            px1=max(0,px1-pad); py1=max(0,py1-pad)
                                            px2=min(pw,px2+pad); py2=min(ph,py2+pad)
                                            pcrop = crop[py1:py2, px1:px2]
                                            if pcrop.size > 0:
                                                plate_text, plate_conf = core._ocr_plate(pcrop)
                                except Exception:
                                    pass

                            # cross-camera global ID assignment
                            global_id, is_new = reid.match_or_register(
                                vehicle_type = vtype,
                                color        = color,
                                number_plate = plate_text,
                                plate_conf   = plate_conf,
                                crop         = crop,
                                camera_id    = self.camera_id,
                                frame_number = self.frame_count,
                            )

                            # ── crop archive ──────────────────────────────────
                            # canonical best crop
                            best_path = os.path.join(
                                self.crop_dir, f"{global_id}.jpg")
                            # per-camera copy for audit / multi-cam view
                            cam_path = os.path.join(
                                self.crop_dir,
                                f"{global_id}_cam{self.camera_id}.jpg")

                            if not os.path.exists(best_path):
                                _atomic_imwrite(best_path, crop)
                            else:
                                existing = cv2.imread(best_path)
                                if existing is not None:
                                    if (crop.shape[0]*crop.shape[1] >
                                        existing.shape[0]*existing.shape[1]):
                                        _atomic_imwrite(best_path, crop)

                            if not os.path.exists(cam_path):
                                _atomic_imwrite(cam_path, crop)
                            else:
                                existing = cv2.imread(cam_path)
                                if existing is not None:
                                    if (crop.shape[0]*crop.shape[1] >
                                        existing.shape[0]*existing.shape[1]):
                                        _atomic_imwrite(cam_path, crop)

                            # push event
                            self._emit({
                                "type":        "detection",
                                "camera_id":   self.camera_id,
                                "vehicle_id":  global_id,
                                "is_new":      is_new,
                                "vehicle_type":vtype,
                                "color":       color,
                                "number_plate":plate_text,
                                "plate_conf":  plate_conf,
                                "confidence":  round(confidence*100, 2),
                                "bounding_box":{"x1":int(x1),"y1":int(y1),
                                                "x2":int(x2),"y2":int(y2)},
                                "frame":       self.frame_count,
                                "crop_path":   best_path,
                            })

                        # periodic flush — throttled to avoid DB lock storms
                        if self.frame_count % 30 == 0:
                            self._periodic_flush()

                except Exception as e:
                    self.last_error = str(e)
                    self._emit({
                        "type": "error",
                        "camera_id": self.camera_id,
                        "msg": str(e),
                    })
                finally:
                    if cap is not None:
                        cap.release()
                        cap = None

                # graceful file-end handling
                if is_file and not self._stop.is_set():
                    break

                if self._stop.is_set():
                    break

            if self.frame_count % 30 == 0 or self.frame_count > 0:
                self._periodic_flush()

        except Exception as fatal:
            self.status = "ERROR"
            self.error_msg = str(fatal)
            self.last_error = str(fatal)
            self._emit({
                "type": "error",
                "camera_id": self.camera_id,
                "msg": str(fatal),
            })
        finally:
            if cap is not None:
                cap.release()
            self.status = "STOPPED"
            try:
                reid.flush_to_json()
            except Exception:
                pass
            self._emit({
                "type": "camera_offline",
                "camera_id": self.camera_id,
                "status": "STOPPED",
            })

    # ── helpers ───────────────────────────────────────────────────────────────

    def _periodic_flush(self):
        """Flush registry JSON (throttled, avoids DB lock storms)."""
        try:
            reid.flush_to_json()
        except Exception:
            pass


# ── manager ───────────────────────────────────────────────────────────────────

class MultiCameraManager:
    """
    Manages N cameras. All share the same global reid registry.
    Supports starting 20–30 cameras from a config list in seconds.
    """

    def __init__(self):
        self.workers: dict[str, CameraWorker] = {}
        self.event_queue = queue.Queue(maxsize=5000)
        core.ensure_db()

    # ── high-level API ─────────────────────────────────────────────────────────

    def add_camera(self, camera_id, source, frame_skip=3, reconnect=True):
        """Add and immediately start a camera."""
        cid = str(camera_id)
        if cid in self.workers and self.workers[cid].is_alive():
            return False
        worker = CameraWorker(
            camera_id=cid,
            source=source,
            event_queue=self.event_queue,
            frame_skip=frame_skip,
            reconnect=reconnect,
        )
        self.workers[cid] = worker
        worker.start()
        return True

    def add_cameras_batch(self, cameras: list) -> int:
        """
        Add many cameras at once.

        cameras: list of dicts:
            {"id": "CAM_01", "source": 0}
            {"id": "GATE_N",  "source": "rtsp://..."}
            {"id": "VID_03",  "source": "input/videos/cam3.mp4",
             "frame_skip": 5}
        Returns number of cameras started.
        """
        count = 0
        for cam in cameras:
            cid = str(cam.get("id", cam.get("camera_id", "")))
            if not cid:
                continue
            source = cam.get("source", 0)
            fs = int(cam.get("frame_skip", 3))
            if self.add_camera(cid, source, frame_skip=fs):
                count += 1
        return count

    def add_cameras_from_json(self, path: str) -> int:
        """Load a JSON list of camera configs and start them all."""
        import json as _json
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding="utf-8") as f:
            cameras = _json.load(f)
        if isinstance(cameras, dict):
            cameras = list(cameras.get("cameras", []))
        return self.add_cameras_batch(cameras)

    def remove_camera(self, camera_id):
        cid = str(camera_id)
        if cid in self.workers:
            self.workers[cid].stop()

    def stop_all(self):
        for w in self.workers.values():
            w.stop()

    def camera_statuses(self) -> dict:
        out = {}
        for cid, w in self.workers.items():
            out[cid] = {
                "status":    w.status,
                "frames":    w.frame_count,
                "source":    str(w.source),
                "alive":     w.is_alive(),
                "error":     w.error_msg or None,
                "last_error": w.last_error,
            }
        return out

    def camera_status_summary(self) -> str:
        lines = []
        for cid, w in self.workers.items():
            status = w.status
            marker = "●" if w.is_alive() and status == "RUNNING" else "○"
            lines.append(f"  {marker} {cid:12s}  {status:8s}  "
                         f"frames={w.frame_count}")
        return "\n".join(lines)

    def reconnect_all(self):
        for w in self.workers.values():
            if not w.is_alive():
                self.add_camera(w.camera_id, w.source)

    def active_count(self) -> int:
        return sum(1 for w in self.workers.values() if w.is_alive())

    def get_events(self, max_events=80) -> list:
        """Non-blocking drain of event queue. Returns list of event dicts."""
        events = []
        for _ in range(max_events):
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def get_all_vehicles(self) -> list:
        return reid.get_all()

    def total_vehicles(self) -> int:
        return reid.total_vehicles()

    def multi_camera_summary(self) -> dict:
        return reid.multi_camera_stats()

    def flush(self):
        reid.flush_to_json()