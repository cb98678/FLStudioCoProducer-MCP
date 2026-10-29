"""The beat grid of a song from a beat tracker's beats and downbeats: tempo, meter, drift, bar lines, and mapping between seconds and bars.

Built for beat_this output (runners/mir_runner.py), which gives beat and downbeat times at 50 frames a second (20 ms steps). The tempo is the slope
of a straight line through the beat times (index against seconds), which is far finer than the median beat interval: on the Friends stems
(2026-10-25) the median interval read 107.14 bpm and the line 108.504, against 108.478 measured by hand earlier, and the downbeat before the drums
came in at 27.34 s against the hand-found 27.3085. A song is "drifting" when a bar's own tempo
leaves the global one by more than drift_pct; a live recording then needs a tempo map, not one stretch ratio.
"""
from __future__ import annotations

import numpy as np

DRIFT_PCT = 3.0


def beat_indexes(beats: list[float]) -> np.ndarray:
    """Beat numbers for beat times with gaps: each interval counts as the whole number of median beats it spans, so a beat the tracker missed
    (a break, a half-time bar) does not slow the fitted tempo down. A dubstep render read 110.7 bpm by plain index and 140 this way (2026-10-25)."""
    t = np.asarray(beats, dtype=float)
    period = float(np.median(np.diff(t)))
    steps = np.maximum(1, np.round(np.diff(t) / period)).astype(int)
    return np.concatenate([[0], np.cumsum(steps)])


def line_tempo(beats: list[float], tol_ms: float = 35.0) -> tuple[float, float]:
    """(bpm, residual ms): the period that puts the most beats on one grid (searched within 6 % of the median interval), then least squares
    through (grid number, time) of those inlier beats; residual is the RMS distance of all beats from the line. Numbering by the grid rather
    than by counting gaps means one doubled or missed beat cannot shift every later number (renders read 124.2 for 124 and 183 for 174
    when counted, 2026-10-25)."""
    t = np.asarray(beats, dtype=float)
    if len(t) < 4:
        raise ValueError("need at least 4 beats")
    p0 = float(np.median(np.diff(t)))
    best = max(((grid_fit(t, p, tol_ms)["share"], -abs(p - p0), p) for p in p0 * np.linspace(0.94, 1.06, 241)))
    period = best[2]
    phase = grid_fit(t, period, tol_ms)["phase_s"]
    k = np.round((t - phase) / period)
    inl = np.abs(t - phase - k * period) <= max(tol_ms / 1000, 0.25 * period)
    if inl.sum() < 4:
        inl = np.ones(len(t), dtype=bool)
    slope, icpt = np.polyfit(k[inl], t[inl], 1)
    res = t - (slope * k + icpt)
    return float(60.0 / slope), float(np.sqrt(np.mean(res ** 2)) * 1000)


def beats_per_bar(beats: list[float], downbeats: list[float]) -> list[int]:
    b, d = np.asarray(beats), np.asarray(downbeats)
    return [int(((b >= d[i] - 0.03) & (b < d[i + 1] - 0.03)).sum()) for i in range(len(d) - 1)]


def grid_fit(times: list[float], period_s: float, tol_ms: float = 35.0) -> dict:
    """How well events sit on a grid of period_s at its best phase (the phase that puts the most events within tol_ms; each event's own phase
    is a candidate): the share within tol_ms of a grid line and the median distance. Checks a known tempo directly, so a missed or doubled
    beat costs one event, not the whole fit (a render's tempo check)."""
    t = np.asarray(times, dtype=float)
    if len(t) == 0 or period_s <= 0:
        return {"share": 0.0, "median_ms": None, "events": 0}
    res = t % period_s
    cand = res[:: max(1, len(res) // 200)]  # at most about 200 candidate phases
    d = np.abs((cand[:, None] - res[None, :] + period_s / 2) % period_s - period_s / 2)
    phase = float(cand[int(np.argmax((d <= tol_ms / 1000).sum(axis=1)))])
    err = (t - phase + period_s / 2) % period_s - period_s / 2
    return {"share": round(float(np.mean(np.abs(err) <= tol_ms / 1000)), 3), "median_ms": round(float(np.median(np.abs(err)) * 1000), 1), "events": len(t),
            "phase_s": round(phase, 4)}


def analyze(beats: list[float], downbeats: list[float], drift_pct: float = DRIFT_PCT) -> dict:
    """Tempo, meter and drift. Bars are the downbeat times; odd_bars lists bar indexes whose beat count differs from the meter. The tempo is the
    straighter of two lines, through the beats or through the downbeats (tempo_from): on syncopated renders the beats wander while the bars
    stay regular (a dnb render at 174: beats read 190.8 with 2.2 s of residual, its bars sat 1.379 s apart, 2026-10-25)."""
    if len(downbeats) < 3:
        raise ValueError("need at least 3 downbeats")
    bpm, res_ms = line_tempo(beats)
    counts = beats_per_bar(beats, downbeats)
    meter = int(np.bincount(counts).argmax()) if counts else 4
    tempo_from = "beats"
    if len(downbeats) >= 4:
        bars_per_min, bar_res = line_tempo(downbeats)
        if bar_res < res_ms:  # both are times off a straight line, in ms
            bpm, res_ms, tempo_from = bars_per_min * meter, bar_res, "downbeats"
    d = np.asarray(downbeats, dtype=float)
    bar_bpm = [round(float(60.0 * c / (d[i + 1] - d[i])), 2) for i, c in enumerate(counts) if c]
    dev = [abs(x - bpm) / bpm * 100 for x in bar_bpm]
    # a bar is drifting only when its neighbours agree: one odd bar is a tracking slip, a run of them is the band moving
    smooth = np.convolve(np.asarray(dev), np.ones(4) / 4, mode="valid") if len(dev) >= 4 else np.asarray(dev)
    steady = res_ms < 0.08 * 60000.0 / bpm  # beats within 8 % of a beat of one straight line: a tempo you can trust
    return {"bpm": round(bpm, 3), "residual_ms": round(res_ms, 1), "steady": bool(steady), "tempo_from": tempo_from, "meter": meter, "bars": [round(float(x), 4) for x in d],
            "bar_count": len(d), "origin_s": round(float(d[0]), 4), "odd_bars": [i for i, c in enumerate(counts) if c != meter],
            "bar_bpm": bar_bpm, "max_drift_pct": round(float(smooth.max()), 2) if len(smooth) else 0.0,
            "drifting": bool(len(smooth) and smooth.max() > drift_pct)}


def time_to_bar(grid: dict, t: float) -> float:
    """Fractional bar index (0 at the first downbeat) of a time in seconds, by the downbeats; outside them, by the global tempo."""
    d = np.asarray(grid["bars"])
    bar_s = 60.0 * grid["meter"] / grid["bpm"]
    if t < d[0]:
        return (t - d[0]) / bar_s
    if t >= d[-1]:
        return len(d) - 1 + (t - d[-1]) / bar_s
    i = int(np.searchsorted(d, t, side="right") - 1)
    return i + (t - d[i]) / (d[i + 1] - d[i])


def bar_to_time(grid: dict, bar: float) -> float:
    d = np.asarray(grid["bars"])
    bar_s = 60.0 * grid["meter"] / grid["bpm"]
    if bar < 0:
        return float(d[0] + bar * bar_s)
    i = int(bar)
    if i >= len(d) - 1:
        return float(d[-1] + (bar - (len(d) - 1)) * bar_s)
    return float(d[i] + (bar - i) * (d[i + 1] - d[i]))


def first_bar_after(grid: dict, t: float) -> int:
    """Index of the first bar line at or after t seconds (for example the first bar where the drums are in)."""
    d = np.asarray(grid["bars"])
    return int(np.searchsorted(d, t - 0.05))
