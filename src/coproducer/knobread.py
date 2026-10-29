"""Read an FL Studio knob's position from a screenshot: the coloured value arc drawn around the knob.

FL's plugin and editor knobs (Newtone's CENTER, VARIATION and TRANS among them) draw a coloured arc from the 7 o'clock end of their travel to
the current value; the travel is 270 degrees, 7 o'clock to 5 o'clock. The value is where the arc ends, as a fraction of the travel. Dragging
a knob does not map pixels to value evenly (the same 105 px moved VARIATION 57 % up and 36 % down, 2026-10-29), so a recipe sets a knob by
reading it back after each drag instead of trusting one drag.
"""
from __future__ import annotations

import math

import numpy as np

TRAVEL_DEG = 270.0


def knob_value(rgb: np.ndarray, cx: int, cy: int, radii: tuple[int, ...] = (16, 17, 18, 19, 20), min_sat: float = 0.45,
               min_val: float = 0.45) -> float:
    """0..1 position of the knob centred at (cx, cy): the furthest coloured pixel along its arc, sampled every 2.5 degrees on a few radii."""
    a = rgb.astype(float) / 255.0
    last = None
    for r in radii:
        for tenths in range(-1450, 1451, 25):
            ang = math.radians(tenths / 10.0)
            x, y = int(round(cx + r * math.sin(ang))), int(round(cy - r * math.cos(ang)))
            if not (0 <= y < a.shape[0] and 0 <= x < a.shape[1]):
                continue
            px = a[y, x, :3]
            mx, mn = float(px.max()), float(px.min())
            if mx >= min_val and (mx - mn) / max(mx, 1e-9) >= min_sat and (last is None or tenths > last):
                last = tenths
    if last is None:
        return 0.0
    return round(min(1.0, max(0.0, (last / 10.0 + TRAVEL_DEG / 2) / TRAVEL_DEG)), 3)


def drag_pixels(current: float, target: float, px_per_travel: float = 200.0) -> int:
    """Vertical drag (negative is up, which raises the value) estimated to move a knob from current to target."""
    return int(round(-(target - current) * px_per_travel))
