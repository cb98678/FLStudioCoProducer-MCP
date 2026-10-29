"""Does a rendered part land on the grid? Onset times in a solo render against the times its notes say.

Render one part alone (every other channel disabled), read the note times from the project (`Flp.note_ticks`), and compare. A part whose offsets
are small and steady is on the grid; the feel problem is then the sound or the pattern, not the timing.
"""
from __future__ import annotations

import numpy as np

from . import flpfile


def note_times_s(f: flpfile.Flp, channel_id: int) -> list[float]:
    """Seconds at which the notes of a channel start, from the playlist and the project tempo."""
    spt = 60.0 / f.tempo() / flpfile.TICKS_PER_BEAT
    return [t * spt for t in f.note_ticks(channel_id)]


def _envelope(x: np.ndarray, rate: int, smooth_ms: float) -> np.ndarray:
    m = np.abs(x).max(axis=1) if x.ndim > 1 else np.abs(x)
    w = max(1, int(smooth_ms / 1000.0 * rate))
    return np.convolve(m, np.ones(w) / w, mode="same")


def onset_offsets_ms(x: np.ndarray, rate: int, expected_s: list[float], lead_s: float = 0.05, span_s: float = 0.35, frac: float = 0.25,
                     floor: float = 1e-3, smooth_ms: float = 2.0) -> list[float | None]:
    """Offset in ms of the first rise past `frac` of the local peak, for each expected time (None where the render is silent there).
    The search runs from lead_s before the expected time to span_s after it, or to the next expected time if that is sooner."""
    env = _envelope(x, rate, smooth_ms)
    times = sorted(set(round(t, 6) for t in expected_s))
    out: list[float | None] = []
    for i, t in enumerate(times):
        a = max(0, int((t - lead_s) * rate))
        stop = t + span_s if i + 1 == len(times) else min(t + span_s, times[i + 1] - 0.005)
        seg = env[a : max(a + 1, int(stop * rate))]
        if seg.size == 0 or seg.max() < floor:
            out.append(None)
            continue
        out.append(round(((a + int(np.argmax(seg > frac * seg.max()))) / rate - t) * 1000.0, 2))
    return out


def summarize(offsets: list[float | None], tolerance_ms: float = 10.0) -> dict:
    """Median, spread and the number of notes outside the tolerance."""
    got = np.array([o for o in offsets if o is not None], dtype=float)
    if got.size == 0:
        return {"notes": len(offsets), "heard": 0}
    return {"notes": len(offsets), "heard": int(got.size), "missing": len(offsets) - int(got.size), "median_ms": round(float(np.median(got)), 2),
            "p10_ms": round(float(np.percentile(got, 10)), 2), "p90_ms": round(float(np.percentile(got, 90)), 2), "max_abs_ms": round(float(np.abs(got).max()), 2),
            "outside_tolerance": int((np.abs(got - np.median(got)) > tolerance_ms).sum()), "on_grid": bool(abs(np.median(got)) <= tolerance_ms and np.abs(got - np.median(got)).max() <= tolerance_ms)}
