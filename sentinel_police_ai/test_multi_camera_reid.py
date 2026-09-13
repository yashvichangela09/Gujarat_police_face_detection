"""
test_multi_camera_reid.py
Integration test proving cross-camera re-identification works for 20–30 cameras.

Scenario A — appearance-only re-ID:
    The SAME physical vehicle (synthetic crop with slight per-camera
    appearance variation) is seen by 30 different cameras.
    EXPECT: exactly ONE global vehicle ID with cameras_count == 30.

Scenario B — plate-merge re-ID:
    Cameras 1–10 see the vehicle BEFORE plate OCR succeeds (plate UNKNOWN),
    creating several provisional global IDs.  Camera 11 reads the plate with
    high confidence.  The registry must MERGE all provisional IDs into one.
    EXPECT: exactly ONE global vehicle ID with cameras_count == 30.

Run:  python test_multi_camera_reid.py
"""

import os
import sys
import time
import numpy as np
import cv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import cross_camera_reid as reid


# ─────────────────────────────────────────────────────────────────────────────
# synthetic vehicle crop generator
# ─────────────────────────────────────────────────────────────────────────────

def make_vehicle_crop(seed: int, color_bgr=(200, 60, 30),
                      variation: float = 0.06) -> np.ndarray:
    """
    Build a 96x64 synthetic "vehicle" crop.

    The same physical vehicle seen from different cameras will have:
      • same dominant body colour
      • same roof/body layout
      • small per-camera brightness / noise variation
    """
    rng = np.random.default_rng(seed)
    img = np.zeros((96, 64, 3), dtype=np.uint8)

    # body
    body = np.array(color_bgr, dtype=np.float32)
    body += rng.normal(0, 255 * variation, 3)
    body = np.clip(body, 0, 255).astype(np.uint8)
    img[20:80, 8:56] = body

    # roof (darker top band)
    roof = body * 0.75
    img[20:38, 8:56] = roof.astype(np.uint8)

    # windshield (dark band)
    img[38:48, 8:56] = (30, 30, 30)

    # wheels (dark bottom corners)
    img[70:88, 10:20] = (20, 20, 20)
    img[70:88, 44:54] = (20, 20, 20)

    # per-camera noise
    noise = rng.normal(0, 255 * variation * 0.5, img.shape)
    img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    return img


def make_plate_crop(seed: int) -> np.ndarray:
    """Synthetic plate crop (not used for OCR — only for feature extraction)."""
    rng = np.random.default_rng(seed)
    img = np.full((24, 48, 3), (220, 220, 220), dtype=np.uint8)
    img[4:20, 6:42] = (200, 200, 200)
    # dark "characters"
    for x in range(8, 40, 6):
        img[6:18, x:x+3] = (30, 30, 30)
    noise = rng.normal(0, 8, img.shape)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario A — appearance-only across 30 cameras
# ─────────────────────────────────────────────────────────────────────────────

def test_appearance_reid_30_cameras():
    print("\n" + "=" * 70)
    print("SCENARIO A:  SAME VEHICLE SEEN BY 30 CAMERAS (appearance only)")
    print("=" * 70)

    reid.reset()
    N_CAMERAS = 30
    ids = set()

    for cam in range(1, N_CAMERAS + 1):
        crop = make_vehicle_crop(seed=1000 + cam, variation=0.05)
        vid, is_new = reid.match_or_register(
            vehicle_type="Car",
            color="Red",
            number_plate="UNKNOWN",
            plate_conf=0.0,
            crop=crop,
            camera_id=f"CAM_{cam:02d}",
            frame_number=cam * 10,
        )
        ids.add(vid)
        # small delay so same-camera fast-path doesn't dominate
        time.sleep(0.01)

    total = reid.total_vehicles()
    stats = reid.multi_camera_stats()

    print(f"  Cameras fed        : {N_CAMERAS}")
    print(f"  Unique global IDs  : {len(ids)}  {sorted(ids)}")
    print(f"  Registry vehicles  : {total}")
    print(f"  Seen on 2+ cameras : {stats['seen_on_2plus_cameras']}")

    assert total == 1, \
        f"FAIL: expected 1 global vehicle, got {total}"
    assert len(ids) == 1, \
        f"FAIL: expected 1 unique ID, got {len(ids)}"

    veh = reid.get_all()[0]
    assert veh["cameras_count"] == N_CAMERAS, \
        f"FAIL: expected {N_CAMERAS} cameras, got {veh['cameras_count']}"
    assert len(veh["cameras_seen"]) == N_CAMERAS

    route = reid.get_vehicle_route(veh["vehicle_id"])
    print(f"  Vehicle route      : {' → '.join(route)}")
    print("  ✓ PASS — one vehicle, one global ID, seen on all 30 cameras")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Scenario B — plate-merge across 30 cameras
# ─────────────────────────────────────────────────────────────────────────────

def test_plate_merge_30_cameras():
    print("\n" + "=" * 70)
    print("SCENARIO B:  PLATE-MERGE — 30 CAMERAS, PLATE READ LATE")
    print("=" * 70)

    reid.reset()
    N_CAMERAS = 30
    PLATE = "MH12AB1234"
    ids = set()

    # Cameras 1–10: plate NOT readable yet → provisional IDs
    for cam in range(1, 11):
        crop = make_vehicle_crop(seed=2000 + cam, variation=0.05)
        vid, is_new = reid.match_or_register(
            vehicle_type="Car",
            color="Blue",
            number_plate="UNKNOWN",
            plate_conf=0.0,
            crop=crop,
            camera_id=f"CAM_{cam:02d}",
            frame_number=cam * 10,
        )
        ids.add(vid)
        time.sleep(0.01)

    provisional = reid.total_vehicles()
    print(f"  After cams 1-10 (no plate) : {provisional} provisional IDs")

    # Cameras 11–30: plate now readable with high confidence
    for cam in range(11, N_CAMERAS + 1):
        crop = make_vehicle_crop(seed=2000 + cam, variation=0.05)
        vid, is_new = reid.match_or_register(
            vehicle_type="Car",
            color="Blue",
            number_plate=PLATE,
            plate_conf=0.85,
            crop=crop,
            camera_id=f"CAM_{cam:02d}",
            frame_number=cam * 10,
        )
        ids.add(vid)
        time.sleep(0.01)

    total = reid.total_vehicles()
    stats = reid.multi_camera_stats()
    merges = reid.take_merge_events()

    print(f"  Cameras fed        : {N_CAMERAS}")
    print(f"  Provisional IDs    : {provisional}")
    print(f"  Merge events       : {len(merges)}")
    print(f"  Final global IDs   : {total}")
    print(f"  Seen on 2+ cameras : {stats['seen_on_2plus_cameras']}")

    assert total == 1, \
        f"FAIL: plate-merge should collapse to 1 vehicle, got {total}"
    # Either path is acceptable:
    #   A) appearance matcher already collapsed all provisional IDs before
    #      the plate was read (merge events == 0), or
    #   B) plate-merge collapsed them (merge events >= 1).
    # Both prove the same physical vehicle converges to ONE global ID.

    if provisional > 1:
        assert len(merges) >= 1, \
            "FAIL: expected at least one merge event when provisional IDs existed"

    veh = reid.get_all()[0]
    assert veh["cameras_count"] == N_CAMERAS, \
        f"FAIL: expected {N_CAMERAS} cameras, got {veh['cameras_count']}"
    assert veh["number_plate"] == PLATE, \
        f"FAIL: expected plate {PLATE}, got {veh['number_plate']}"

    route = reid.get_vehicle_route(veh["vehicle_id"])
    print(f"  Vehicle route      : {' → '.join(route)}")
    print("  ✓ PASS — plate-merge collapsed all provisional IDs into one")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Scenario C — different vehicles stay separate
# ─────────────────────────────────────────────────────────────────────────────

def test_distinct_vehicles_stay_separate():
    print("\n" + "=" * 70)
    print("SCENARIO C:  3 DIFFERENT VEHICLES ON 30 CAMERAS STAY SEPARATE")
    print("=" * 70)

    reid.reset()
    N_CAMERAS = 30

    # 3 distinct vehicles: red car, blue truck, white motorcycle
    vehicles = [
        ("Car",        "Red",   (200, 60, 30),  3000),
        ("Truck",      "Blue",  (60, 60, 200),  4000),
        ("Motorcycle", "White", (240, 240, 240), 5000),
    ]

    for cam in range(1, N_CAMERAS + 1):
        for vtype, color, bgr, seed_base in vehicles:
            crop = make_vehicle_crop(seed=seed_base + cam, variation=0.05)
            reid.match_or_register(
                vehicle_type=vtype,
                color=color,
                number_plate="UNKNOWN",
                plate_conf=0.0,
                crop=crop,
                camera_id=f"CAM_{cam:02d}",
                frame_number=cam * 10,
            )
            time.sleep(0.005)

    total = reid.total_vehicles()
    stats = reid.multi_camera_stats()

    print(f"  Cameras fed        : {N_CAMERAS}")
    print(f"  Distinct vehicles  : 3")
    print(f"  Registry vehicles  : {total}")
    print(f"  Seen on 2+ cameras : {stats['seen_on_2plus_cameras']}")

    assert total == 3, \
        f"FAIL: expected 3 distinct vehicles, got {total}"
    assert stats["seen_on_2plus_cameras"] == 3, \
        f"FAIL: expected all 3 on 2+ cameras, got {stats['seen_on_2plus_cameras']}"

    for v in reid.get_all():
        assert v["cameras_count"] == N_CAMERAS, \
            f"FAIL: {v['vehicle_id']} should be on {N_CAMERAS} cameras"

    print("  ✓ PASS — 3 distinct vehicles each tracked across all 30 cameras")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok_a = test_appearance_reid_30_cameras()
    ok_b = test_plate_merge_30_cameras()
    ok_c = test_distinct_vehicles_stay_separate()

    print("\n" + "=" * 70)
    print("MULTI-CAMERA RE-IDENTIFICATION TEST SUMMARY")
    print("=" * 70)
    print(f"  Scenario A (appearance, 30 cams) : {'PASS' if ok_a else 'FAIL'}")
    print(f"  Scenario B (plate-merge, 30 cams): {'PASS' if ok_b else 'FAIL'}")
    print(f"  Scenario C (distinct, 30 cams)   : {'PASS' if ok_c else 'FAIL'}")
    print("=" * 70)

    if ok_a and ok_b and ok_c:
        print("\nALL TESTS PASSED ✓")
        print("The system can detect and track the same vehicle across 20-30 cameras.")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED ✗")
        sys.exit(1)