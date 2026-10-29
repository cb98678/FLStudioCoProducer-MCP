"""Track the notes of a monophonic bass stem and read the key and a root per bar from them. numpy and scipy only.

Heuristic: normalized autocorrelation on a 8 kHz low-passed copy, parabolic peak refinement, median smoothing, then segmentation by pitch jumps
and silence. Good for a single bass line; chords or noisy stems need a real transcriber (Basic Pitch runner).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def track_pitch(x: np.ndarray, rate: int, hop_s: float = 0.01, fmin: float = 32.0, fmax: float = 260.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (times, midi_float, level) per frame; midi is NaN where unvoiced. x is mono."""
    target = 8000
    y = signal.resample_poly(x, target, rate) if rate != target else x
    b, a = signal.butter(4, 400 / (target / 2), "low")
    y = signal.lfilter(b, a, y)
    win, hop = int(0.085 * target), int(hop_s * target)
    lag_lo, lag_hi = int(target / fmax), int(target / fmin)
    n = max(0, (len(y) - win) // hop)
    midi = np.full(n, np.nan)
    level = np.zeros(n)
    nfft = 1 << (2 * win - 1).bit_length()
    taper = np.hanning(win)
    for i in range(n):
        seg = y[i * hop : i * hop + win] * taper
        e = float(np.sqrt(np.mean(seg**2)))
        level[i] = e
        if e < 1e-4:
            continue
        f = np.fft.rfft(seg, nfft)
        ac = np.fft.irfft(f * np.conj(f))[: lag_hi + 2]
        ac = ac / (ac[0] + 1e-12)
        seg_ac = ac[lag_lo : lag_hi + 1]
        peaks = np.flatnonzero((seg_ac[1:-1] >= seg_ac[:-2]) & (seg_ac[1:-1] > seg_ac[2:])) + 1  # interior peaks only: the edge of the lag range
        if not len(peaks):  # is high for any tone well below fmax and is not a pitch
            continue
        p = int(peaks[np.argmax(seg_ac[peaks])])
        if seg_ac[p] < 0.45:
            continue
        k = p + lag_lo
        if 1 <= p < len(seg_ac) - 1:
            l, c, r = seg_ac[p - 1], seg_ac[p], seg_ac[p + 1]
            d = l - 2 * c + r
            k = k + (0.5 * (l - r) / d if d != 0 else 0.0)
        # prefer the lowest lag that is nearly as strong (avoids octave-down errors the other way round)
        midi[i] = 69 + 12 * np.log2(target / k / 440.0)
    times = (np.arange(n) * hop + win / 2) / target
    return times, midi, level


def notes_from_track(times: np.ndarray, midi: np.ndarray, level: np.ndarray, min_len: float = 0.07, jump: float = 0.7) -> list[dict]:
    """Group frames into notes {start, end, pitch (int midi), cents, level}. A note ends on silence or a pitch jump over `jump` semitones."""
    sm = midi.copy()
    ok = ~np.isnan(midi)
    if ok.sum() > 5:
        filled = np.where(ok, midi, 0.0)
        med = signal.medfilt(filled, 5)
        sm = np.where(ok, med, np.nan)
    notes: list[dict] = []
    start = None
    ref = None
    vals: list[float] = []
    lv: list[float] = []
    hop = float(times[1] - times[0]) if len(times) > 1 else 0.01

    def close(end_i: int) -> None:
        nonlocal start, vals, lv
        if start is not None and len(vals) * hop >= min_len:
            p = float(np.median(vals))
            notes.append({"start": float(times[start] - hop / 2), "end": float(times[end_i] + hop / 2), "pitch": int(round(p)),
                          "cents": round((p - round(p)) * 100, 1), "level": float(np.mean(lv))})
        start, vals, lv = None, [], []

    for i, v in enumerate(sm):
        if np.isnan(v):
            close(i - 1)
            ref = None
            continue
        if start is not None and abs(v - ref) > jump:
            close(i - 1)
        if start is None:
            start, ref = i, v
        vals.append(v)
        lv.append(level[i])
        ref = float(np.median(vals[-15:]))
    close(len(sm) - 1)
    return notes


def estimate_key(notes: list[dict]) -> dict:
    """Best major or minor key from the duration-weighted pitch classes of the bass notes."""
    pc = np.zeros(12)
    for n in notes:
        pc[n["pitch"] % 12] += (n["end"] - n["start"]) * (0.5 + n["level"] / (max(m["level"] for m in notes) + 1e-12))
    best = None
    for tonic in range(12):
        for mode, prof in (("major", MAJOR), ("minor", MINOR)):
            r = float(np.corrcoef(np.roll(prof, tonic), pc)[0, 1])
            if best is None or r > best["score"]:
                best = {"tonic": NAMES[tonic], "tonic_pc": tonic, "mode": mode, "score": round(r, 4)}
    return {**best, "pitch_class_share": {NAMES[i]: round(float(pc[i] / max(pc.sum(), 1e-12)), 3) for i in range(12)}}


def roots_per_bar(notes: list[dict], bpm: float, origin_s: float, bars: int) -> list[int | None]:
    """The pitch class that holds the most note time in each bar (bar 0 starts at origin_s), None for empty bars."""
    bar_s = 240.0 / bpm
    out: list[int | None] = []
    for b in range(bars):
        t0, t1 = origin_s + b * bar_s, origin_s + (b + 1) * bar_s
        w = np.zeros(12)
        for n in notes:
            ov = min(n["end"], t1) - max(n["start"], t0)
            if ov > 0:
                w[n["pitch"] % 12] += ov
        out.append(int(np.argmax(w)) if w.sum() > 0.2 * bar_s else None)
    return out
