import cv2
import numpy as np


# ==========================================
# VEHICLE TYPE
# ==========================================

def get_vehicle_type(class_id, image=None):

    vehicle_types = {
        2: "Car",
        3: "Motorcycle",
        5: "Bus",
        7: "Truck"
    }

    # Optional auto-rickshaw check
    if class_id == 2 and image is not None:
        if looks_like_auto_rickshaw(image):
            return "Auto Rickshaw"

    return vehicle_types.get(class_id, "Vehicle")


# ==========================================
# AUTO-RICKSHAW HEURISTIC
# ==========================================

def looks_like_auto_rickshaw(image):

    if image is None or image.size == 0:
        return False

    h, w = image.shape[:2]

    if h == 0 or w == 0:
        return False

    aspect_ratio = w / h

    # Conservative rule
    if aspect_ratio < 1.15:
        return True

    return False


# ==========================================
# VEHICLE COLOR
# ==========================================

def get_vehicle_color(image):

    if image is None or image.size == 0:
        return "Unknown"

    image = cv2.resize(image, (160, 160))
    h, w = image.shape[:2]

    # Use central body zone — avoids road, sky, windows
    crop = image[
        int(h * 0.25):int(h * 0.85),
        int(w * 0.15):int(w * 0.85)
    ]

    if crop.size == 0:
        return "Unknown"

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    H = hsv[:, :, 0]
    S = hsv[:, :, 1]
    V = hsv[:, :, 2]
    total = H.size

    # ------------------------------------------
    # NEUTRAL PIXEL RATIOS
    # ------------------------------------------

    white_ratio = np.sum((S < 55) & (V > 150)) / total
    silver_ratio = np.sum((S < 55) & (V >= 100) & (V <= 200)) / total
    black_ratio  = np.sum((V < 55)) / total

    # Neutral pixels = low saturation overall
    neutral_ratio = np.sum(S < 60) / total

    # ------------------------------------------
    # KEY RULE:
    # If most of the crop is desaturated,
    # it's a neutral-coloured vehicle.
    # Don't let a small pocket of blue sky /
    # road reflection decide the color.
    # ------------------------------------------

    if neutral_ratio >= 0.65:
        # Mostly desaturated — decide between
        # white, silver, grey, black
        if white_ratio >= 0.25:
            return "White"
        if black_ratio >= 0.35:
            return "Black"
        if silver_ratio >= 0.35:
            return "Silver"
        return "Grey"

    # ------------------------------------------
    # STANDARD NEUTRAL CHECKS
    # ------------------------------------------

    if white_ratio >= 0.30:
        return "White"

    if black_ratio >= 0.35:
        return "Black"

    if silver_ratio >= 0.35:
        return "Silver"

    # ------------------------------------------
    # COLORED VEHICLE
    # Only count pixels that are genuinely
    # saturated AND bright enough to be paint.
    # ------------------------------------------

    colored = (S > 70) & (V > 50)
    colored_ratio = np.sum(colored) / total

    # If less than 20% of the crop is saturated,
    # it's effectively a neutral car.
    if colored_ratio < 0.20:
        if white_ratio >= 0.20:
            return "White"
        if black_ratio >= 0.25:
            return "Black"
        return "Grey"

    hues = H[colored]

    color_counts = {
        "Red":    int(np.sum((hues < 10) | (hues >= 170))),
        "Orange": int(np.sum((hues >= 10) & (hues < 22))),
        "Yellow": int(np.sum((hues >= 22) & (hues < 38))),
        "Green":  int(np.sum((hues >= 38) & (hues < 85))),
        "Blue":   int(np.sum((hues >= 85) & (hues < 130))),
        "Purple": int(np.sum((hues >= 130) & (hues < 170))),
    }

    dominant = max(color_counts, key=color_counts.get)
    dom_ratio = color_counts[dominant] / len(hues)

    # Require strong dominance to assign a color
    if dom_ratio < 0.55:
        return "Grey"

    return dominant


# ==========================================
# VEHICLE APPEARANCE FINGERPRINT
# ==========================================

def get_appearance_features(image):

    if image is None or image.size == 0:
        return []

    image = cv2.resize(image, (64, 64))

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    histogram = cv2.calcHist(
        [hsv],
        [0, 1],
        None,
        [16, 16],
        [0, 180, 0, 256]
    )

    histogram = cv2.normalize(
        histogram,
        histogram
    )

    return histogram.flatten().tolist()


# ==========================================
# COMPLETE VEHICLE ATTRIBUTES
# ==========================================

def extract_vehicle_attributes(
    vehicle_image,
    class_id
):

    vehicle_type = get_vehicle_type(
        class_id,
        vehicle_image
    )

    color = get_vehicle_color(
        vehicle_image
    )

    appearance_features = get_appearance_features(
        vehicle_image
    )

    return {
        "vehicle_type": vehicle_type,
        "color": color,
        "appearance_features": appearance_features
    }