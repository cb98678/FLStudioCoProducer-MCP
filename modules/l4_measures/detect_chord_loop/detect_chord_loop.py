from __future__ import annotations

import math

from coproducer.result import Result, ok

_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_SHAPES = {"": (0, 4, 7), "m": (0, 3, 7), "dim": (0, 3, 6), "sus2": (0, 2, 7), "sus4": (0, 5, 7),
           "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "7": (0, 4, 7, 10)}


def _name(weights: list) -> str:
    if sum(weights) <= 0:
        return "N"
    best, label = -1e9, "N"
    for root in range(12):
        for suffix, shape in _SHAPES.items():
            inside = sum(weights[(root + i) % 12] for i in shape)
            score = inside - 0.7 * (sum(weights) - inside) - 0.08 * len(shape) * sum(weights)
            if score > best:
                best, label = score, _NAMES[root] + suffix
    return label


def detect_chord_loop(notes: list[dict], beats_per_bar: int = 4) -> Result:
    """Name one chord per bar from the notes sounding in it, then find the shortest repeating chord loop.

    loop is null when no repeat of at least two cycles matches 90 percent of the bars.
    """
    bars = math.ceil(max(n["start"] + n["duration"] for n in notes) / beats_per_bar - 1e-9) if notes else 0
    weights = [[0.0] * 12 for _ in range(bars)]
    for n in notes:
        for b in range(int(n["start"] // beats_per_bar), int((n["start"] + n["duration"] - 1e-9) // beats_per_bar) + 1):
            lo, hi = max(n["start"], b * beats_per_bar), min(n["start"] + n["duration"], (b + 1) * beats_per_bar)
            weights[b][n["pitch"] % 12] += max(0.0, hi - lo) * n.get("velocity", 100)
    chords = [_name(w) for w in weights]
    loop = None
    for p in range(1, bars // 2 + 1):
        match = sum(chords[i] == chords[i % p] for i in range(bars)) / bars
        if match >= 0.9 and loop is None:
            loop = {"bars": p, "progression": chords[:p], "match": round(match, 3)}
    return ok({"chords": chords, "loop": loop})
