"""
cross_camera_reid.py
Global vehicle registry for cross-camera re-identification.

Each camera runs its own per-camera tracker (local IDs).
When a new detection arrives from any camera, this registry:
  1. Tries to match it against all known global vehicles using:
     - Number plate (strongest signal - exact plate match wins)
     - Vehicle type gate (must match exactly)
     - Color-attribute agreement (bonus / penalty)
     - Multi-part HSV + edge-layout appearance feature
  2. If a match is found  -> reuse the existing global VEH_XXXX
  3. If no match          -> register new global VEH_XXXX

Plate-merge:
  A vehicle initially seen by Cam-01 before plate OCR succeeds may be
  assigned VEH_0001, while the same vehicle on Cam-12 is assigned
  VEH_0007.  When a later, higher-confidence plate is read that proves
  both entries are the SAME vehicle, the registry automatically MERGES
  VEH_0007 into VEH_0001 (cameras_seen, timeline and features union).
  This guarantees the same physical vehicle converges to a single ID
  even across 20-30 cameras where plate detection is intermittent.

Thread-safe:
  One module-level RLock guards every public mutating API.  The hot path
  (match_or_register) keeps all matching and index maintenance inside a
  single critical section so two cameras can never corrupt the index.
"""

import threading
import numpy as np
import cv2
import time
import os
import json
import re
from collections import deque

# global lock (RLock permits helper fn calls inside critical section)
_lock = threading.RLock()

# global vehicle registry
# vehicle_id -> {
#   "vehicle_id":   str,
#   "vehicle_type": str,
#   "color":        str,
#   "number_plate": str,
#   "plate_conf":   float,
#   "feature":      np.ndarray | None,     # latest appearance descriptor
#   "template":     np.ndarray | None,     # median across recent samples
#   "feature_bank": deque of feature vecs,
#   "cameras_seen": set of camera_id,
#   "first_seen":   float (time.time()),
#   "last_seen":    float,
#   "frames_seen":  int,
#   "crop_path":    str | None,
#   "timeline":     list of events,
# }
_registry: dict = {}
_next_id: int   = 1

# search indexes
# plate_clean -> set[vehicle_id]
_plate_index: dict = {}
# vehicle_type -> set[vehicle_id]
_type_index:  dict = {}

# Recent same-camera match cache :  prevents flapping between two near-duplicate
# entries within a short time window while a vehicle sits at one camera.
_recent_by_cam: dict = {}

# Merge events produced by plate-confirmed merges.  Camera-workers consume this
# via take_merge_events() so the dashboard can display "merged into VEH_0001".
_merge_events = deque(maxlen=200)

# similarity thresholds
PLATE_MATCH_MIN    = 0.80    # lowest confident-plate score accepted as match
APPEAR_MATCH_SIM   = 0.62    # appearance sim required when no plate available
HIGH_CONF_PLATE    = 0.62    # plate OCR conf above this is trusted for merging
SAME_CAM_REUSE_SIM = 0.80    # re-match within same camera window
SAME_CAM_REUSE_SEC = 8.0      # seconds for same-camera fast-path

# appearance sub-parts
FEATURE_BANK_SZ    = 12
TIMELINE_CAP       = 300

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CROP_DIR   = os.path.join(BASE_DIR, "output", "vehicle_crops")


# appearance descriptor

def _normalize_histogram(h: np.ndarray) -> np.ndarray:
    """Make a nonneg histogram L2-normalised & flatten to float32."""
    h = h.astype(np.float32)
    norm = float(np.sqrt(np.sum(h * h)))
    if norm < 1e-8:
        return np.zeros_like(h)
    return (h / norm).flatten()


def _grad_orientation_hist(gray: np.ndarray, bins: int = 16):
    """HOG-lite: gradient-magnitude weighted orientation histogram."""
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    hist = np.zeros(bins, dtype=np.float32)
    step = 360.0 / bins
    for i in range(bins):
        lo, hi = i * step, (i + 1) * step
        mask = (ang >= lo) & (ang < hi)
        hist[i] = float(np.sum(mag[mask]))
    return _normalize_histogram(hist)


def _block_color_stats(hsv: np.ndarray, rows: int = 2, cols: int = 2):
    """Mean per-quadrant HSV - preserves colour layout (roof / body)."""
    h, w = hsv.shape[:2]
    parts = []
    for r in range(rows):
        y0, y1 = int(h * r / rows), int(h * (r + 1) / rows)
        for c in range(cols):
            x0, x1 = int(w * c / cols), int(w * (c + 1) / cols)
            blk = hsv[y0:y1, x0:x1]
            if blk.size == 0:
                parts += [0.0, 0.0, 0.0]
                continue
            means = blk.reshape(-1, 3).mean(axis=0)
            parts += [float(means[0]) / 180.0,
                      float(means[1]) / 255.0,
                      float(means[2]) / 255.0]
    return np.array(parts, dtype=np.float32)


def _make_feature(crop):
    """
    Compact multi-part appearance descriptor for re-identification.

    Returns a dict { 'desc': np.ndarray(concatenated),
                     'hsv':  ...,
                     'grad': ...,
                     'blocks': ... }
    so similarity can weight individual sub-parts independently.

    Returns None when the crop is unusable.
    """
    if crop is None or crop.size == 0:
        return None
    try:
        small = cv2.resize(crop, (64, 64))
        hsv   = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        H, S, V = cv2.split(hsv)
        # 8x4x4 = 128 bins - far more robust than 16x8x8 for
        # vehicles with large uniform body regions (sparse-histogram problem).
        hist_hsv = cv2.calcHist([H, S, V], [0, 1, 2], None,
                                [8, 4, 4],
                                [0, 180, 0, 256, 0, 256])
        grad   = _grad_orientation_hist(gray)
        blocks = _block_color_stats(hsv)

        # flatten to 3 independent float32 arrays
        vec_hsv  = _normalize_histogram(hist_hsv)
        vec_grad = grad.astype(np.float32)
        desc = np.concatenate([vec_hsv, vec_grad, blocks]).astype(np.float32)

        return {
            "desc":   desc,
            "hsv":    vec_hsv,
            "grad":   vec_grad,
            "blocks": blocks,
        }
    except Exception:
        return None


def _sim_feature(q, t) -> float:
    """
    Combined appearance similarity between two _make_feature dicts.
    HSV histogram 40%  +  colour-layout 35%  +  edge texture 25%.
    """
    if q is None or t is None:
        return 0.0
    # both histograms are L2-normalised non-negative -> dot product is a clean
    # correlation in [0, 1] and safer than cv2.compareHist cross-version.
    try:
        hsv_sim = float(np.dot(q["hsv"], t["hsv"]))
    except Exception:
        hsv_sim = 0.0
    blocks_sim = 1.0 - float(np.linalg.norm(q["blocks"] - t["blocks"])) \
        if q["blocks"].size else 0.0
    grad_sim  = float(np.dot(q["grad"], t["grad"])) \
        if q["grad"].size else 0.0
    blocks_sim = float(np.clip(blocks_sim, 0.0, 1.0))
    grad_sim   = float(np.clip(grad_sim, 0.0, 1.0))
    # HSV histogram 40%  +  colour-layout 35%  +  edge texture 25% -
    # block-colour layout and edge texture are far more stable across cameras
    # than a sparse global HSV histogram on uniform-bodied vehicles.
    return float(np.clip(0.40*hsv_sim + 0.35*blocks_sim + 0.25*grad_sim,
                         0.0, 1.0))


def _sim_legacy(f1, f2):
    """Backward-compatible scalar histogram similarity (public use)."""
    if f1 is None or f2 is None:
        return 0.0
    return _sim_feature(f1, f2)


def _plate_clean(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


def _new_id() -> str:
    global _next_id
    vid = f"VEH_GLOBAL_{_next_id:04d}"
    _next_id += 1
    return vid


# index maintenance

def _index_entry(vid: str) -> None:
    e = _registry.get(vid)
    if e is None:
        return
    plate = _plate_clean(e.get("number_plate", ""))
    if plate and plate != "UNKNOWN":
        _plate_index.setdefault(plate, set()).add(vid)
    _type_index.setdefault(e["vehicle_type"], set()).add(vid)


def _unindex_entry(vid: str) -> None:
    e = _registry.get(vid)
    if e is None:
        return
    plate = _plate_clean(e.get("number_plate", ""))
    if plate in _plate_index:
        _plate_index[plate].discard(vid)
        if not _plate_index[plate]:
            del _plate_index[plate]
    tset = _type_index.get(e["vehicle_type"], set())
    tset.discard(vid)
    if not tset:
        _type_index.pop(e["vehicle_type"], None)


def _refresh_entry_index(vid: str) -> None:
    """Call after plate / type changes on an existing entry."""
    _unindex_entry(vid)
    _index_entry(vid)


def _color_agreement(entry_color: str, query_color: str) -> int:
    """+1 agree | 0 unknown/neutral-boundary | -1 conflict"""
    if not entry_color or not query_color:
        return 0
    if entry_color == "Unknown" or query_color == "Unknown":
        return 0
    if entry_color == "Grey" and query_color in ("Silver", "White", "Black"):
        return 0    # neutral colours frequently cross-classified across cameras
    if query_color == "Grey" and entry_color in ("Silver", "White", "Black"):
        return 0
    if entry_color == query_color:
        return 1
    return -1


# recent-camera fast path (anti-flap)

def _recent_same_camera(camera_id: str, qfeature, qtype: str,
                        color: str) -> tuple:
    """
    If the same camera reported a near-identical feature within the last few
    seconds, strongly prefer re-using that camera's last known global ID.
    Prevents one continuous vehicle from flicker-creating two adjacent IDs.
    """
    rec = _recent_by_cam.get(str(camera_id))
    if not rec:
        return None, 0.0
    vid, last_ts, feats, rtype, rcolor = rec
    if time.time() - last_ts > SAME_CAM_REUSE_SEC:
        return None, 0.0
    if rtype != qtype:
        return None, 0.0
    sim = _sim_feature(feats, qfeature)
    if sim < SAME_CAM_REUSE_SIM:
        return None, 0.0
    if _color_agreement(rcolor, color) < 0:
        return None, 0.0
    return vid, sim


def _store_recent(camera_id: str, vid: str, qfeature, qtype: str,
                  color: str) -> None:
    _recent_by_cam[str(camera_id)] = (
        vid, time.time(), qfeature, qtype, color)


# merge engine

def _update_entry_feature(entry, feature) -> None:
    """Update per-vehicle template bank and robust median template."""
    if feature is None:
        return
    bank = entry.setdefault("feature_bank", deque(maxlen=FEATURE_BANK_SZ))
    bank.append(feature)
    entry["feature"] = feature

    # robust element-wise median across the bank -> tolerates bad single frames
    if len(bank) >= 2:
        try:
            keys  = ("hsv", "grad", "blocks")
            med = {k: np.median(
                np.stack([b[k] for b in bank]), axis=0
            ).astype(np.float32) for k in keys}
            entry["template"] = med
        except Exception:
            entry["template"] = feature
    else:
        entry["template"] = feature


def _template_of(entry):
    return entry.get("template") or entry.get("feature")


def _append_timeline(entry, camera_id: str, frame_number: int) -> None:
    tl = entry.setdefault("timeline", [])
    tl.append({
        "vehicle_id":  entry["vehicle_id"],
        "camera_id":   str(camera_id),
        "frame":       int(frame_number),
        "time":        time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    if len(tl) > TIMELINE_CAP:
        del tl[: len(tl) - TIMELINE_CAP]


def merge_vehicle(target_id: str, source_id: str) -> bool:
    """
    Merge source vehicle into target vehicle (target keeps lowest/oldest ID).

    Both entries must exist.  Plate confirmed same physical vehicle.
    cameras_seen / timeline / feature banks are unioned.  Returns True only
    when a source -> target merge actually happened.
    """
    if target_id == source_id:
        return False
    with _lock:
        if target_id not in _registry or source_id not in _registry:
            return False
        dst = _registry[target_id]
        src = _registry[source_id]

        # union camera coverage
        dst["cameras_seen"] |= src["cameras_seen"]
        dst["frames_seen"]  += src.get("frames_seen", 0)
        if src.get("number_plate") and \
                _plate_clean(src["number_plate"]) not in ("", "UNKNOWN"):
            sconf = src.get("plate_conf", 0.0)
            dconf = dst.get("plate_conf", 0.0)
            if sconf > dconf:
                dst["number_plate"] = src["number_plate"]
                dst["plate_conf"]   = sconf

        if dst.get("color", "Unknown") == "Unknown":
            dst["color"] = src.get("color", "Unknown")

        # union feature banks
        src_bank = list(src.get("feature_bank", [])) or \
            ([src["feature"]] if src.get("feature") is not None else [])
        dst_bank = dst.setdefault("feature_bank", deque(maxlen=FEATURE_BANK_SZ))
        for f in src_bank:
            dst_bank.append(f)
        if src.get("feature") is not None:
            dst["feature"] = src["feature"]
        _update_entry_feature(dst, dst["feature"])

        # union timeline
        dst_tl = dst.setdefault("timeline", [])
        for ev in src.get("timeline", []):
            dst_tl.append(ev)
        if len(dst_tl) > TIMELINE_CAP:
            del dst_tl[: len(dst_tl) - TIMELINE_CAP]

        # keep best crop
        if src.get("crop_path") and os.path.exists(str(src["crop_path"])):
            dst_path = dst.get("crop_path")
            if not dst_path or not os.path.exists(str(dst_path)):
                dst["crop_path"] = src["crop_path"]

        # remove source from registry and indexes
        _unindex_entry(source_id)
        _registry.pop(source_id, None)

        # keep source crop file, dashboard can still display it while listed
        _merge_events.append({
            "vehicle_id":  target_id,
            "merged_from": source_id,
            "time":        time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cameras":     sorted(dst["cameras_seen"]),
        })
        return True


def take_merge_events() -> list:
    """Drain merge notifications (safe for camera-workers / dashboard)."""
    with _lock:
        out = list(_merge_events)
        _merge_events.clear()
        return out


# public API

def reset():
    """Clear registry. Call when starting a fresh session."""
    global _registry, _next_id, _recent_by_cam, _plate_index, _type_index
    with _lock:
        _registry       = {}
        _next_id        = 1
        _recent_by_cam  = {}
        _plate_index    = {}
        _type_index     = {}
        _merge_events.clear()


def match_or_register(
    vehicle_type: str,
    color: str,
    number_plate: str,
    plate_conf: float,
    crop,            # BGR numpy array or None
    camera_id,       # int or str identifying the camera
    frame_number: int = 0,
    crop_path: str = None,
) -> tuple:
    """
    Match a detection against the global registry or create a new entry.

    Returns (vehicle_id: str, is_new: bool)

    Plate-confirmed identity collisions are resolved by auto-merging two
    existing global entries into one - this is the key mechanism that makes
    one physical car keep a single VEH_XXXX across 20-30 cameras even when
    the earliest cameras couldn't read the plate yet.
    """
    plate     = _plate_clean(number_plate)
    has_plate = plate not in ("", "UNKNOWN")
    qfeature  = _make_feature(crop)
    now       = time.time()

    with _lock:
        # fast path: same camera, almost identical appearance
        if qfeature is not None:
            same_vid, same_sim = _recent_same_camera(
                camera_id, qfeature, vehicle_type, color)
            if same_vid is not None:
                e = _registry.get(same_vid)
                if e is not None:
                    _store_recent(camera_id, same_vid, qfeature,
                                  vehicle_type, color)
                    e["last_seen"]    = now
                    e["frames_seen"] += 1
                    e["cameras_seen"].add(str(camera_id))
                    _update_entry_feature(e, qfeature)
                    if color not in ("Unknown", "Grey") and \
                            e.get("color", "Unknown") == "Unknown":
                        e["color"] = color
                    _append_timeline(e, camera_id, frame_number)
                    if crop_path:
                        e["crop_path"] = crop_path
                    return same_vid, False

        # candidate shortlist
        candidates = []

        if has_plate:
            # strongest signal: exact plate index
            for vid in _plate_index.get(plate, set()):
                cand = _registry.get(vid)
                if cand is not None and cand["vehicle_type"] == vehicle_type:
                    candidates.append(vid)

        # when no plate (or no index hit), fall back to type shortlist
        if not candidates:
            for vid in _type_index.get(vehicle_type, set()):
                cand = _registry.get(vid)
                if cand is None or not cand["vehicle_type"] == vehicle_type:
                    continue
                # avoid returning the same-camera stale candidate if plate now
                # says something different
                candidates.append(vid)

        # scoring
        best_id    = None
        best_score = 0.0

        for vid in candidates:
            entry  = _registry[vid]
            entry_plate = _plate_clean(entry.get("number_plate", ""))

            score = 0.0

            # exact plate match (verified)
            if has_plate and entry_plate == plate:
                app_sim = _sim_feature(qfeature, _template_of(entry))
                agree   = _color_agreement(
                    entry.get("color", "Unknown"), color)
                if agree < 0:
                    continue      # plate same but colours conflict -> plate OCR error
                score = 0.85 + 0.15 * app_sim
                if agree == 0:
                    score -= 0.02
                score += min(0.06, float(plate_conf) / 2000.0)

            # appearance-only candidate
            else:
                app_sim = _sim_feature(qfeature, _template_of(entry))
                agree   = _color_agreement(
                    entry.get("color", "Unknown"), color)
                if agree < 0:
                    continue
                score = app_sim
                if agree == 1:
                    score += 0.05
                elif agree == 0:
                    pass

            if score > best_score:
                best_score = score
                best_id    = vid

        if best_id is None:
            # still allow low-sim exact-plate when feature absent
            if has_plate:
                for vid in _plate_index.get(plate, set()):
                    entry = _registry.get(vid)
                    if entry is None:
                        continue
                    if entry_plate := _plate_clean(
                            entry.get("number_plate", "")) == plate:
                        best_id = vid
                        break

        threshold = PLATE_MATCH_MIN if has_plate else APPEAR_MATCH_SIM

        # plate-merge of pre-existing duplicate identities
        merged = False
        if best_id is not None and has_plate:
            # Are there OTHER existing registries that also carry this exact
            # plate? If so they are duplicates of best_id that were created
            # before plate OCR succeeded.  Merge them now.
            for other_vid in list(_plate_index.get(plate, ())):
                if other_vid == best_id:
                    continue
                other = _registry.get(other_vid)
                if other is None:
                    continue
                if other["vehicle_type"] != vehicle_type:
                    continue
                if float(other.get("plate_conf", 0.0)) >= \
                        HIGH_CONF_PLATE or float(plate_conf) >= \
                        HIGH_CONF_PLATE:
                    merge_vehicle(best_id, other_vid)
                    merged = True

        is_new = (best_id is None or best_score < threshold)

        if is_new and not merged:
            vid   = _new_id()
            entry = {
                "vehicle_id":   vid,
                "vehicle_type": vehicle_type,
                "color":        color,
                "number_plate": plate if has_plate else "UNKNOWN",
                "plate_conf":   float(plate_conf),
                "feature":      None,
                "template":     None,
                "feature_bank": deque(maxlen=FEATURE_BANK_SZ),
                "cameras_seen": {str(camera_id)},
                "first_seen":   now,
                "last_seen":    now,
                "frames_seen":  1,
                "crop_path":    crop_path,
                "timeline":     [],
            }
            _update_entry_feature(entry, qfeature)
            _registry[vid] = entry
            _index_entry(vid)
            _append_timeline(entry, camera_id, frame_number)
            if qfeature is not None:
                _store_recent(camera_id, vid, qfeature,
                              vehicle_type, color)

            return vid, True

        # matched existing entry
        vid   = best_id
        entry = _registry[vid]
        entry["cameras_seen"].add(str(camera_id))
        entry["last_seen"]    = now
        entry["frames_seen"] += 1
        _append_timeline(entry, camera_id, frame_number)

        # plate upgrade & reindex if changed
        old_plate = _plate_clean(entry.get("number_plate", ""))
        if has_plate and (not old_plate or float(plate_conf) >
                          float(entry.get("plate_conf", 0.0))):
            entry["number_plate"] = plate
            entry["plate_conf"]   = float(plate_conf)
            if old_plate != plate:
                _refresh_entry_index(vid)

        if entry.get("color", "Unknown") == "Unknown" and \
                color not in ("Unknown", ""):
            entry["color"] = color

        if qfeature is not None:
            _update_entry_feature(entry, qfeature)
            _store_recent(camera_id, vid, qfeature, vehicle_type, color)

        # best crop only replaced when both plate & larger frame appear
        if crop_path:
            old_crop = entry.get("crop_path")
            if not old_crop or not os.path.exists(str(old_crop)):
                entry["crop_path"] = crop_path
            else:
                a = os.path.getsize(str(old_crop))
                b = os.path.getsize(str(crop_path)) if os.path.exists(
                    str(crop_path)) else 0
                if b > a * 1.3:
                    entry["crop_path"] = crop_path

        return vid, False


# registry inspection

def _serialise_entry(entry, include_feature=False):
    d = dict(entry)
    d["cameras_seen"]  = sorted(d["cameras_seen"])
    d["cameras_count"] = len(d["cameras_seen"])
    if not include_feature:
        d["feature"]      = None
        d["template"]     = None
        d["feature_bank"] = None
    d["timeline"] = d.get("timeline", [])[-TIMELINE_CAP:]
    d["first_seen_iso"] = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(d["first_seen"]))
    d["last_seen_iso"]  = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(d["last_seen"]))
    return d


def get_all() -> list:
    """Return all registry entries as a list of dicts (JSON-safe)."""
    with _lock:
        return [_serialise_entry(e) for e in _registry.values()]


def get_vehicle(vehicle_id: str) -> dict | None:
    with _lock:
        entry = _registry.get(vehicle_id)
        return _serialise_entry(entry) if entry is not None else None


def total_vehicles() -> int:
    with _lock:
        return len(_registry)


def multi_camera_stats() -> dict:
    """Summary of how many vehicles were confirmed on >=2 cameras."""
    with _lock:
        multi = [v for v in _registry.values() if len(v["cameras_seen"]) >= 2]
        sub = {}
        for v in _registry.values():
            sub.setdefault(v["vehicle_type"], 0)
            sub[v["vehicle_type"]] += 1
        return {
            "registry_vehicles": len(_registry),
            "seen_on_2plus_cameras": len(multi),
            "seen_on_2plus_vehicles": [
                {
                    "vehicle_id":   v["vehicle_id"],
                    "vehicle_type": v["vehicle_type"],
                    "color":        v.get("color", "Unknown"),
                    "number_plate": v.get("number_plate", "UNKNOWN"),
                    "cameras":      sorted(v["cameras_seen"]),
                    "cameras_count":len(v["cameras_seen"]),
                }
                for v in sorted(multi, key=lambda x: -len(x["cameras_seen"]))
            ][:100],
            "vehicle_types": sub,
        }


def get_vehicle_route(vehicle_id: str) -> list:
    """Chronological camera sequence for a vehicle (its full journey)."""
    with _lock:
        entry = _registry.get(vehicle_id)
        if entry is None:
            return []
        cams  = [ev["camera_id"] for ev in entry.get("timeline", [])]
        seq   = []
        prev  = None
        for c in cams:
            if c != prev:
                seq.append(c)
                prev = c
        return seq


def flush_to_json():
    """Persist registry to final_vehicle_records.json."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    records = []
    with _lock:
        for entry in _registry.values():
            d = _serialise_entry(entry)
            records.append({
                "vehicle_id":           d["vehicle_id"],
                "tracking_id":          d["vehicle_id"],
                "vehicle_type":         d["vehicle_type"],
                "color":                d["color"],
                "number_plate":         d["number_plate"],
                "plate_confidence":     d["plate_conf"],
                "detection_confidence": 0.0,
                "cameras_seen":         d["cameras_seen"],
                "cameras_count":        d["cameras_count"],
                "frames_seen":          d["frames_seen"],
                "appearance":           {},
                "first_seen":           d["first_seen_iso"],
                "last_seen":            d["last_seen_iso"],
                "route":                get_vehicle_route(d["vehicle_id"]),
                "timeline":             d["timeline"],
                "last_updated":         time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
    path = os.path.join(OUTPUT_DIR, "final_vehicle_records.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)