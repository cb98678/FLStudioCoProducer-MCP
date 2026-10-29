"""Describe a single note and compare two notes, to match a synth patch to a generated sound by measurement instead of by ear.

describe_tone reports fundamental, harmonic levels relative to it, decay time to minus 20 dB and spectral centroid.
compare_tones gives the differences and a short list of what to change on the patch. Taste is still the human's call.
"""
from __future__ import annotations

import numpy as np

TOL = {"fundamental_cents": 25.0, "h2_db": 4.0, "h3_db": 5.0, "decay_ratio": 0.35, "centroid_ratio": 0.3}


def describe_tone(x: np.ndarray, sr: int, fmin: float = 20.0, fmax: float = 500.0) -> dict:
    x = x.mean(1) if x.ndim > 1 else x
    env = np.sqrt(np.convolve(x**2, np.ones(441) / 441, mode="same"))
    peak = int(np.argmax(env))
    start = peak + int(0.05 * sr)
    seg = x[start : start + int(0.25 * sr)]
    if len(seg) < sr // 20:
        seg = x[peak : peak + int(0.25 * sr)]
    n = 1 << int(np.ceil(np.log2(len(seg) * 8)))
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
    f = np.fft.rfftfreq(n, 1 / sr)
    band = (f >= fmin) & (f <= fmax)
    f0 = float(f[band][int(np.argmax(spec[band]))])

    def level(hz: float) -> float:
        m = (f > hz * 0.97) & (f < hz * 1.03)
        return float(20 * np.log10(spec[m].max() + 1e-12)) if m.any() else -120.0

    base = level(f0)
    below = np.where(env[peak:] < env[peak] * 0.1)[0]
    decay = float(below[0] / sr) if len(below) else float(len(x[peak:]) / sr)
    cent = float((f * spec).sum() / (spec.sum() + 1e-12))
    return {"fundamental_hz": round(f0, 2), "h2_db": round(level(2 * f0) - base, 1), "h3_db": round(level(3 * f0) - base, 1),
            "decay_s": round(decay, 3), "centroid_hz": round(cent, 1)}


def compare_tones(target: dict, candidate: dict) -> dict:
    cents = 1200 * np.log2(candidate["fundamental_hz"] / target["fundamental_hz"])
    d = {"fundamental_cents": round(float(cents), 1), "h2_db": round(candidate["h2_db"] - target["h2_db"], 1),
         "h3_db": round(candidate["h3_db"] - target["h3_db"], 1),
         "decay_ratio": round(candidate["decay_s"] / max(target["decay_s"], 1e-6), 2),
         "centroid_ratio": round(candidate["centroid_hz"] / max(target["centroid_hz"], 1e-6), 2)}
    todo = []
    if abs(d["fundamental_cents"]) > TOL["fundamental_cents"]:
        todo.append("shift the note by %+.0f cents (about %+.1f semitones; check the patch's own transpose)" % (-d["fundamental_cents"], -d["fundamental_cents"] / 100))
    if abs(d["h2_db"]) > TOL["h2_db"] or abs(d["h3_db"]) > TOL["h3_db"]:
        todo.append("harmonics are %s than the target: %s the patch's brightness or saturation" % ("stronger" if d["h2_db"] + d["h3_db"] > 0 else "weaker", "lower" if d["h2_db"] + d["h3_db"] > 0 else "raise"))
    if abs(d["decay_ratio"] - 1) > TOL["decay_ratio"]:
        todo.append("decay is %.1fx the target: %s the release or amp envelope" % (d["decay_ratio"], "shorten" if d["decay_ratio"] > 1 else "lengthen"))
    if abs(d["centroid_ratio"] - 1) > TOL["centroid_ratio"] and not todo:
        todo.append("overall tone is %s than the target" % ("brighter" if d["centroid_ratio"] > 1 else "darker"))
    return {"differences": d, "match": not todo, "adjust": todo}
