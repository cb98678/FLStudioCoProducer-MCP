"""Find and classify drum hits in a drum stem, fit them to a tempo grid and turn them into piano-roll note rows.

Heuristic and offline: numpy and scipy only. Classes are kick, snare, hat (hats include cymbals and shakers). Accuracy depends on the stem; the
synthetic test pins the mechanics, a real stem needs a listen. Note rows are [start_beat, dur_beats, key, vel] as `tools/flp_tool.py add-notes` expects.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

BANDS = {"low": (30.0, 130.0), "body": (130.0, 450.0), "snap": (1800.0, 6000.0), "hat": (7000.0, 16000.0)}


def _band_flux(x: np.ndarray, rate: int, n_fft: int = 1024, hop: int = 256) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    f, t, z = signal.stft(x, rate, nperseg=n_fft, noverlap=n_fft - hop, boundary=None)
    mag = np.log1p(30.0 * np.abs(z))
    flux = np.maximum(np.diff(mag, axis=1), 0.0)
    out = np.zeros(flux.shape[1])
    for lo, hi in ((30, 130), (130, 450), (1800, 6000), (7000, 16000)):
        sel = (f >= lo) & (f < hi)
        band = flux[sel].sum(axis=0)
        out += band / (band.max() + 1e-9)
    return out, t[1:], f


def detect_hits(x: np.ndarray, rate: int, min_gap_s: float = 0.045, rel_threshold: float = 0.12) -> list[dict]:
    """Return hits as dicts {t, strength, kind, low, body, snap, hat} (energies in the 60 ms after the onset, linear). x is mono."""
    flux, times, _ = _band_flux(x, rate)
    if len(flux) < 8:
        return []
    flux = flux - np.median(flux)
    height = rel_threshold * flux.max()
    hop_s = float(times[1] - times[0])
    peaks, _ = signal.find_peaks(flux, height=height, distance=max(1, int(min_gap_s / hop_s)))
    win = int(0.06 * rate)
    hits = []
    for p in peaks:
        i = int(times[p] * rate)
        seg = x[i : i + win]
        if len(seg) < win // 2:
            continue
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
        fr = np.fft.rfftfreq(len(seg), 1.0 / rate)
        e = {k: float(spec[(fr >= lo) & (fr < hi)].sum()) for k, (lo, hi) in BANDS.items()}
        hits.append({"t": float(times[p]), "strength": float(np.sqrt(np.mean(seg**2))), **e})
    top = max((h["strength"] for h in hits), default=0.0)
    for h in hits:
        h["strength"] = h["strength"] / top if top else 0.0
        h["kind"] = classify(h)
    return hits


def classify(h: dict) -> str:
    """kick: low band dominates. hat: highs dominate the low and body bands together. otherwise snare."""
    total = h["low"] + h["body"] + h["snap"] + h["hat"] + 1e-12
    if h["low"] / total > 0.45:
        return "kick"
    if h["hat"] / total > 0.55 and (h["body"] + h["snap"]) / total < 0.35:
        return "hat"
    return "snare"


def fit_grid(times: list[float], bpm_guess: float, search: float = 0.04, steps_per_beat: int = 4) -> tuple[float, float]:
    """Refine the tempo (within +-4 percent of the guess) and find the grid offset in seconds that put hits closest to 16th steps."""
    t = np.asarray(times, dtype=float)
    if t.size < 8:
        return bpm_guess, 0.0
    best = (1e9, bpm_guess, 0.0)
    for bpm in np.linspace(bpm_guess * (1 - search), bpm_guess * (1 + search), 161):
        step = 60.0 / bpm / steps_per_beat
        ph = (t / step) * 2 * np.pi
        c, s = np.cos(ph).mean(), np.sin(ph).mean()
        offset = (np.arctan2(s, c) / (2 * np.pi)) * step
        resid = ((t - offset) / step) - np.round((t - offset) / step)
        err = float(np.mean(np.abs(resid)))
        if err < best[0]:
            best = (err, float(bpm), float(offset % step))
    return best[1], best[2]


def beat_zero(hits: list[dict], bpm: float, offset: float, steps_per_beat: int = 4, origin: float | None = None) -> float:
    """Time in seconds of beat 0: `origin` when given, else the grid line nearest the first hit."""
    if origin is not None:
        return origin
    if not hits:
        return offset
    step = 60.0 / bpm / steps_per_beat
    return offset + round((min(h["t"] for h in hits) - offset) / step) * step


def to_note_rows(hits: list[dict], bpm: float, offset: float, keys: dict[str, int], steps_per_beat: int = 4,
                 origin: float | None = None) -> dict[str, list[list]]:
    """Snap hits to the grid; one row list per kind: [start_beat, dur_beats, key, vel]. Duplicate steps keep the loudest.
    Beat 0 is `origin` seconds, by default the first hit; the grid only fixes phase within a 16th, so pass origin to line up bar one."""
    step = 1.0 / steps_per_beat
    offset = beat_zero(hits, bpm, offset, steps_per_beat, origin)
    rows: dict[str, dict[float, list]] = {k: {} for k in keys}
    for h in hits:
        if h["kind"] not in keys:
            continue
        beat = round(((h["t"] - offset) * bpm / 60.0) / step) * step
        if beat < 0:
            continue
        vel = int(max(20, min(127, round(30 + 97 * h["strength"]))))
        old = rows[h["kind"]].get(beat)
        if old is None or vel > old[3]:
            rows[h["kind"]][beat] = [float(beat), step, keys[h["kind"]], vel]
    return {k: [rows[k][b] for b in sorted(rows[k])] for k in rows}
