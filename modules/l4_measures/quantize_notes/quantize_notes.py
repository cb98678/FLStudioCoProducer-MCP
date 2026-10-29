from __future__ import annotations

from coproducer.result import Result, ok


def quantize_notes(notes: list[dict], grid_beats: float = 0.25, strength: float = 1.0, quantize_length: bool = False) -> Result:
    """Snap note starts (and optionally lengths) toward a grid in beats. strength 1.0 snaps fully, 0.5 moves halfway.

    A note never becomes shorter than one grid step when its length is quantized.
    """
    out = []
    for n in notes:
        snapped = round(n["start"] / grid_beats) * grid_beats
        start = round(n["start"] + (snapped - n["start"]) * strength, 6)
        dur = n["duration"]
        if quantize_length:
            dur = max(grid_beats, round(dur / grid_beats) * grid_beats)
        out.append({**n, "start": max(0.0, start), "duration": round(dur, 6)})
    return ok(out)
