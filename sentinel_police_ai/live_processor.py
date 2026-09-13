"""
live_processor.py

Runs the AI pipeline in a background thread for video files and CCTV streams.
The dashboard creates one LiveProcessor instance and calls start/stop.
"""

import cv2
import threading
import queue
import time
import os

import pipeline_core as core


class LiveProcessor:
    """
    Background worker that reads frames from a video or camera source,
    runs the detection pipeline, and posts results to an output queue.
    """

    def __init__(self):
        self._thread:    threading.Thread | None = None
        self._stop_evt:  threading.Event         = threading.Event()
        self._cap:       cv2.VideoCapture | None  = None

        # Queues consumed by the dashboard
        self.frame_queue:  queue.Queue = queue.Queue(maxsize=2)
        self.result_queue: queue.Queue = queue.Queue(maxsize=200)
        self.event_queue:  queue.Queue = queue.Queue(maxsize=500)

        self.status:       str  = "IDLE"
        self.frame_count:  int  = 0
        self.source_label: str  = ""

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC INTERFACE
    # ──────────────────────────────────────────────────────────────────────────

    def start_video(self, video_path: str):
        """Process a video file in the background."""
        self._launch(video_path, label=os.path.basename(video_path),
                     status="PROCESSING VIDEO")

    def start_camera(self, source=0):
        """
        Start a live camera / CCTV stream.
        source can be: 0, 1, or an RTSP URL string.
        """
        label = f"Camera {source}" if isinstance(source, int) else str(source)
        self._launch(source, label=label, status="CCTV ACTIVE")

    def stop(self):
        self._stop_evt.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        if self._cap:
            self._cap.release()
            self._cap = None
        self.status = "IDLE"

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ──────────────────────────────────────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────────────────────────────────────

    def _launch(self, source, label: str, status: str):
        if self.is_running():
            self.stop()

        # reset tracker for new session
        core.reset_tracker()
        core.ensure_db()

        self._stop_evt.clear()
        self.frame_count  = 0
        self.source_label = label
        self.status       = status

        # drain old queues
        for q in (self.frame_queue, self.result_queue, self.event_queue):
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break

        self._thread = threading.Thread(
            target=self._run,
            args=(source,),
            daemon=True,
        )
        self._thread.start()

    def _run(self, source):
        try:
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                self.event_queue.put({
                    "type":    "error",
                    "message": f"Cannot open source: {source}",
                })
                self.status = "IDLE"
                return
            self._cap = cap

            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            is_file = isinstance(source, str) and os.path.isfile(source)

            frame_skip = 2          # process every Nth frame for speed
            frame_idx  = 0

            while not self._stop_evt.is_set():
                ret, frame = cap.read()
                if not ret:
                    if is_file:
                        break       # video ended
                    # camera hiccup — try again briefly
                    time.sleep(0.05)
                    continue

                frame_idx        += 1
                self.frame_count += 1

                if frame_idx % frame_skip != 0:
                    # Still push a display frame (original, no boxes yet)
                    self._push_frame(frame, [])
                    continue

                # ── run pipeline ──────────────────────────────────────────
                try:
                    detections = core.process_frame(
                        frame,
                        frame_number=self.frame_count,
                        run_plate=True,
                        source_name=self.source_label,
                    )
                except Exception as e:
                    self.event_queue.put({"type": "error", "message": str(e)})
                    detections = []

                # ── save to DB every 30 processed frames ──────────────────
                if self.frame_count % 30 == 0:
                    try:
                        core.save_to_db(detections)
                        core._flush_vehicle_records()
                    except Exception:
                        pass

                # ── annotate and push ─────────────────────────────────────
                annotated = core.annotate_frame(frame, detections)
                self._push_frame(annotated, detections)

                # ── post events ───────────────────────────────────────────
                for d in detections:
                    etype = "NEW VEHICLE" if d["is_new"] else "VEHICLE SEEN"
                    self.event_queue.put({
                        "type":       etype,
                        "vehicle_id": d["vehicle_id"],
                        "vtype":      d["vehicle_type"],
                        "color":      d["color"],
                        "plate":      d["number_plate"],
                        "frame":      self.frame_count,
                    })

                # push result snapshot
                try:
                    self.result_queue.put_nowait(detections)
                except queue.Full:
                    try:
                        self.result_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self.result_queue.put_nowait(detections)

        except Exception as e:
            self.event_queue.put({"type": "error", "message": str(e)})
        finally:
            if self._cap:
                self._cap.release()
                self._cap = None
            # final flush
            try:
                core.save_to_db([])
                core._flush_vehicle_records()
            except Exception:
                pass
            self.status = "IDLE"
            self.event_queue.put({"type": "done", "message": "Processing complete"})

    def _push_frame(self, frame, detections):
        """Put a frame into the display queue, dropping if full."""
        item = (frame, detections)
        try:
            self.frame_queue.put_nowait(item)
        except queue.Full:
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frame_queue.put_nowait(item)
            except queue.Full:
                pass
