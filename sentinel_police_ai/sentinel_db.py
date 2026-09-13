"""
sentinel_db.py
Enhanced database layer for the SENTINEL command-center vehicle intelligence system.

Tables:
  vehicles           - one row per unique global vehicle
  detections         - every detection event (frame-level)
  camera_sightings   - per-camera appearance groups for trajectory
  plates             - ANPR readings
  vehicle_attributes - extracted attributes per vehicle
  watchlist          - plates under surveillance
  alerts             - watchlist match alerts

Relationships:
  vehicle -> many detections
  vehicle -> many camera_sightings
  vehicle -> many plates
  vehicle -> one vehicle_attributes
"""

import sqlite3
import os
import json
import time
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "output")
DATABASE_PATH = os.path.join(DATABASE_DIR, "sentinel_vehicle_database.db")

_BUSY_TIMEOUT_MS = 5000
_db_lock = threading.RLock()


def connect():
    os.makedirs(DATABASE_DIR, exist_ok=True)
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=_BUSY_TIMEOUT_MS / 1000.0,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=%d" % _BUSY_TIMEOUT_MS)
        connection.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass
    return connection


def _now():
    return datetime.now().isoformat(timespec="seconds")


def create_tables():
    connection = connect()
    cursor = connection.cursor()

    # ── vehicles ─────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT UNIQUE,
            tracking_id TEXT,
            vehicle_type TEXT DEFAULT 'Unknown',
            color TEXT DEFAULT 'Unknown',
            number_plate TEXT DEFAULT 'UNKNOWN',
            plate_confidence REAL DEFAULT 0,
            detection_confidence REAL DEFAULT 0,
            first_seen TEXT,
            last_seen TEXT,
            frames_tracked INTEGER DEFAULT 0,
            cameras_seen TEXT DEFAULT '[]',
            route TEXT DEFAULT '[]',
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # ── detections ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            tracking_id TEXT,
            camera_id TEXT,
            camera_location TEXT DEFAULT '',
            frame_number INTEGER DEFAULT 0,
            timestamp TEXT,
            x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER,
            confidence REAL DEFAULT 0,
            vehicle_type TEXT DEFAULT 'Unknown',
            color TEXT DEFAULT 'Unknown',
            number_plate TEXT DEFAULT 'UNKNOWN',
            plate_confidence REAL DEFAULT 0,
            crop_path TEXT,
            speed REAL,
            direction TEXT,
            created_at TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # ── camera_sightings ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS camera_sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            camera_id TEXT,
            camera_location TEXT DEFAULT '',
            first_seen TEXT,
            last_seen TEXT,
            sightings_count INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0,
            crop_path TEXT,
            plate_text TEXT DEFAULT '',
            created_at TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # ── plates ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            number_plate TEXT,
            plate_confidence REAL DEFAULT 0,
            ocr_text TEXT,
            plate_crop_path TEXT,
            camera_id TEXT,
            timestamp TEXT,
            created_at TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # ── vehicle_attributes ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_attributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT UNIQUE,
            vehicle_type TEXT DEFAULT 'Unknown',
            color TEXT DEFAULT 'Unknown',
            appearance_features TEXT DEFAULT '[]',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # ── watchlist ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT UNIQUE,
            label TEXT DEFAULT '',
            severity TEXT DEFAULT 'HIGH',
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # ── alerts ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT,
            vehicle_id TEXT,
            camera_id TEXT,
            camera_location TEXT DEFAULT '',
            severity TEXT DEFAULT 'HIGH',
            message TEXT,
            timestamp TEXT,
            acknowledged INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # ── indexes for performance ──────────────────────────────────────────
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_vehicle ON detections(vehicle_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_camera ON detections(camera_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sight_vehicle ON camera_sightings(vehicle_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_plate_vehicle ON plates(vehicle_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_time ON alerts(timestamp)")

    connection.commit()
    connection.close()


# ═════════════════════════════════════════════════════════════════════════
# VEHICLES
# ═════════════════════════════════════════════════════════════════════════

def upsert_vehicle(vehicle: dict):
    """Insert or update a vehicle row (keyed by vehicle_id)."""
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        now = _now()

        cursor.execute("""
            INSERT INTO vehicles (
                vehicle_id, tracking_id, vehicle_type, color, number_plate,
                plate_confidence, detection_confidence, first_seen, last_seen,
                frames_tracked, cameras_seen, route, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vehicle_id) DO UPDATE SET
                tracking_id=excluded.tracking_id,
                vehicle_type=excluded.vehicle_type,
                color=excluded.color,
                number_plate=excluded.number_plate,
                plate_confidence=excluded.plate_confidence,
                detection_confidence=excluded.detection_confidence,
                last_seen=excluded.last_seen,
                frames_tracked=excluded.frames_tracked,
                cameras_seen=excluded.cameras_seen,
                route=excluded.route,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, (
            vehicle.get("vehicle_id"),
            vehicle.get("tracking_id", vehicle.get("vehicle_id")),
            vehicle.get("vehicle_type", "Unknown"),
            vehicle.get("color", "Unknown"),
            vehicle.get("number_plate", "UNKNOWN"),
            vehicle.get("plate_confidence", 0),
            vehicle.get("detection_confidence", 0),
            vehicle.get("first_seen", now),
            vehicle.get("last_seen", now),
            vehicle.get("frames_tracked", 1),
            json.dumps(vehicle.get("cameras_seen", [])),
            json.dumps(vehicle.get("route", [])),
            vehicle.get("status", "ACTIVE"),
            now,
            now,
        ))
        connection.commit()
        connection.close()


def get_vehicle(vehicle_id: str):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
        row = cursor.fetchone()
        connection.close()
        if row:
            d = dict(row)
            try:
                d["cameras_seen"] = json.loads(d.get("cameras_seen", "[]"))
                d["route"] = json.loads(d.get("route", "[]"))
            except Exception:
                d["cameras_seen"] = []
                d["route"] = []
            return d
        return None


def get_all_vehicles(limit=500):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM vehicles
            ORDER BY COALESCE(last_seen,'') DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        for d in rows:
            try:
                d["cameras_seen"] = json.loads(d.get("cameras_seen", "[]"))
                d["route"] = json.loads(d.get("route", "[]"))
            except Exception:
                d["cameras_seen"] = []
                d["route"] = []
        return rows


def search_vehicles(query: str, limit=200):
    """Search by plate, vehicle_id, type, or color."""
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        q = f"%{query}%"
        cursor.execute("""
            SELECT * FROM vehicles
            WHERE number_plate LIKE ? OR vehicle_id LIKE ?
               OR vehicle_type LIKE ? OR color LIKE ? OR tracking_id LIKE ?
            ORDER BY COALESCE(last_seen,'') DESC
            LIMIT ?
        """, (q, q, q, q, q, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


# ═════════════════════════════════════════════════════════════════════════
# DETECTIONS
# ═════════════════════════════════════════════════════════════════════════

def insert_detection(det: dict):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO detections (
                vehicle_id, tracking_id, camera_id, camera_location,
                frame_number, timestamp, x1, y1, x2, y2, confidence,
                vehicle_type, color, number_plate, plate_confidence,
                crop_path, speed, direction, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            det.get("vehicle_id"),
            det.get("tracking_id", det.get("vehicle_id")),
            det.get("camera_id"),
            det.get("camera_location", ""),
            det.get("frame_number", 0),
            det.get("timestamp", _now()),
            det.get("x1", 0), det.get("y1", 0),
            det.get("x2", 0), det.get("y2", 0),
            det.get("confidence", 0),
            det.get("vehicle_type", "Unknown"),
            det.get("color", "Unknown"),
            det.get("number_plate", "UNKNOWN"),
            det.get("plate_confidence", 0),
            det.get("crop_path"),
            det.get("speed"),
            det.get("direction"),
            _now(),
        ))
        connection.commit()
        connection.close()


def get_detections_for_vehicle(vehicle_id: str, limit=500):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM detections
            WHERE vehicle_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (vehicle_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


# ═════════════════════════════════════════════════════════════════════════
# CAMERA SIGHTINGS
# ═════════════════════════════════════════════════════════════════════════

def upsert_camera_sighting(sighting: dict):
    """One row per (vehicle_id, camera_id). Updates last_seen + count."""
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        existing = cursor.execute("""
            SELECT * FROM camera_sightings
            WHERE vehicle_id = ? AND camera_id = ?
        """, (sighting.get("vehicle_id"), sighting.get("camera_id"))).fetchone()

        if existing:
            cursor.execute("""
                UPDATE camera_sightings SET
                    last_seen = ?,
                    sightings_count = sightings_count + 1,
                    camera_location = ?,
                    confidence = ?,
                    crop_path = ?,
                    plate_text = ?
                WHERE id = ?
            """, (
                sighting.get("last_seen", _now()),
                sighting.get("camera_location", ""),
                sighting.get("confidence", 0),
                sighting.get("crop_path"),
                sighting.get("plate_text", ""),
                existing["id"],
            ))
        else:
            cursor.execute("""
                INSERT INTO camera_sightings (
                    vehicle_id, camera_id, camera_location,
                    first_seen, last_seen, sightings_count,
                    confidence, crop_path, plate_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sighting.get("vehicle_id"),
                sighting.get("camera_id"),
                sighting.get("camera_location", ""),
                sighting.get("first_seen", _now()),
                sighting.get("last_seen", _now()),
                1,
                sighting.get("confidence", 0),
                sighting.get("crop_path"),
                sighting.get("plate_text", ""),
                _now(),
            ))
        connection.commit()
        connection.close()


def get_sightings_for_vehicle(vehicle_id: str):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM camera_sightings
            WHERE vehicle_id = ?
            ORDER BY first_seen ASC
        """, (vehicle_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


# ═════════════════════════════════════════════════════════════════════════
# PLATES
# ═════════════════════════════════════════════════════════════════════════

def insert_plate(plate: dict):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO plates (
                vehicle_id, number_plate, plate_confidence, ocr_text,
                plate_crop_path, camera_id, timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plate.get("vehicle_id"),
            plate.get("number_plate"),
            plate.get("plate_confidence", 0),
            plate.get("ocr_text", ""),
            plate.get("plate_crop_path"),
            plate.get("camera_id"),
            plate.get("timestamp", _now()),
            _now(),
        ))
        connection.commit()
        connection.close()


def get_plates_for_vehicle(vehicle_id: str):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM plates WHERE vehicle_id = ?
            ORDER BY id DESC
        """, (vehicle_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


# ═════════════════════════════════════════════════════════════════════════
# VEHICLE ATTRIBUTES
# ═════════════════════════════════════════════════════════════════════════

def upsert_vehicle_attributes(vehicle_id: str, attrs: dict):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO vehicle_attributes (
                vehicle_id, vehicle_type, color, appearance_features,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(vehicle_id) DO UPDATE SET
                vehicle_type=excluded.vehicle_type,
                color=excluded.color,
                appearance_features=excluded.appearance_features,
                updated_at=excluded.updated_at
        """, (
            vehicle_id,
            attrs.get("vehicle_type", "Unknown"),
            attrs.get("color", "Unknown"),
            json.dumps(attrs.get("appearance_features", [])),
            _now(),
            _now(),
        ))
        connection.commit()
        connection.close()


def get_vehicle_attributes(vehicle_id: str):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM vehicle_attributes WHERE vehicle_id = ?""",
                       (vehicle_id,))
        row = cursor.fetchone()
        connection.close()
        if row:
            d = dict(row)
            try:
                d["appearance_features"] = json.loads(d.get("appearance_features", "[]"))
            except Exception:
                d["appearance_features"] = []
            return d
        return None


# ═════════════════════════════════════════════════════════════════════════
# WATCHLIST
# ═════════════════════════════════════════════════════════════════════════

def add_watchlist_plate(plate: str, label="", severity="HIGH", notes=""):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO watchlist (plate, label, severity, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (plate.upper().strip(), label, severity, notes, _now()))
        connection.commit()
        connection.close()


def remove_watchlist_plate(plate: str):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM watchlist WHERE plate = ?", (plate.upper().strip(),))
        connection.commit()
        connection.close()


def get_watchlist():
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM watchlist ORDER BY severity, plate")
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


def check_watchlist(plate: str):
    """Return matching watchlist entries for a plate, or [] if none."""
    if not plate or plate.upper() in ("UNKNOWN", "", "NONE"):
        return []
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM watchlist WHERE plate = ?",
                       (plate.upper().strip(),))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


# ═════════════════════════════════════════════════════════════════════════
# ALERTS
# ═════════════════════════════════════════════════════════════════════════

def insert_alert(alert: dict):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO alerts (
                plate, vehicle_id, camera_id, camera_location, severity,
                message, timestamp, acknowledged, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.get("plate"),
            alert.get("vehicle_id"),
            alert.get("camera_id"),
            alert.get("camera_location", ""),
            alert.get("severity", "HIGH"),
            alert.get("message", ""),
            alert.get("timestamp", _now()),
            0,
            _now(),
        ))
        connection.commit()
        connection.close()


def get_alerts(limit=100, unacknowledged_only=False):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        if unacknowledged_only:
            cursor.execute("""
                SELECT * FROM alerts WHERE acknowledged = 0
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        else:
            cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        connection.close()
        return rows


def acknowledge_alert(alert_id: int):
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        connection.commit()
        connection.close()


# ═════════════════════════════════════════════════════════════════════════
# STATS
# ═════════════════════════════════════════════════════════════════════════

def get_stats():
    with _db_lock:
        connection = connect()
        cursor = connection.cursor()

        vehicles = cursor.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        detections = cursor.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        plates = cursor.execute(
            "SELECT COUNT(*) FROM plates WHERE number_plate NOT IN ('UNKNOWN','')"
        ).fetchone()[0]
        alerts_un = cursor.execute(
            "SELECT COUNT(*) FROM alerts WHERE acknowledged = 0"
        ).fetchone()[0]
        cameras = cursor.execute(
            "SELECT COUNT(DISTINCT camera_id) FROM detections"
        ).fetchone()[0]
        sightings = cursor.execute(
            "SELECT COUNT(*) FROM camera_sightings WHERE sightings_count >= 2"
        ).fetchone()[0]

        connection.close()
        return {
            "total_vehicles": vehicles,
            "total_detections": detections,
            "total_plates": plates,
            "active_alerts": alerts_un,
            "cameras_with_detections": cameras,
            "multi_camera_vehicles": sightings,
            "watchlist": len(get_watchlist()),
        }


def init_db():
    create_tables()


if __name__ == "__main__":
    init_db()
    print("SENTINEL database ready:", DATABASE_PATH)
    print(json.dumps(get_stats(), indent=2))