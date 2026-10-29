"""Vocal melody as notes, from frame-wise pitch (torchcrepe f0 and periodicity, runners/mir_runner.py) of a separated vocal stem.

A note is a run of voiced frames whose pitch stays within a semitone of its running median; it ends at an unvoiced frame, a jump, or a quiet frame.
The pitch is the median of the run rounded to a semitone, with the median offset in cents kept (a singer a third of a semitone flat stays a note,
the offset says so). Velocity follows the run's level. The notes keep the melody when chords change, give a key estimate that is independent of the
DSP key estimator, and are what the melody-similarity check compares (docs/plan/01-vision-and-spec.md, S-01).
"""
from __future__ import annotations

import numpy as np

# Krumhansl-Kessler key profiles (major, minor), tonic first.
MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)
NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def hz_to_midi(f: np.ndarray) -> np.ndarray:
    return 69.0 + 12.0 * np.log2(np.maximum(np.asarray(f, dtype=float), 1e-6) / 440.0)


def notes_from_f0(f0, periodicity, rms, hop_s: float, offset_s: float = 0.0, min_conf: float = 0.5, min_dur: float = 0.08,
                  jump: float = 0.8, silence_db: float = -45.0) -> list[dict]:
    """[{start, end, pitch, cents, velocity}] in seconds of the file (offset_s added)."""
    f0, per, rms = (np.asarray(v, dtype=float) for v in (f0, periodicity, rms))
    n = min(len(f0), len(per), len(rms))
    f0, per, rms = f0[:n], per[:n], rms[:n]
    level = 20 * np.log10(np.maximum(rms, 1e-9))
    loud_ref = np.percentile(level[per >= min_conf], 95) if (per >= min_conf).any() else 0.0
    voiced = (per >= min_conf) & (f0 > 0) & (level > max(silence_db, loud_ref - 40))
    midi = hz_to_midi(f0)
    out: list[dict] = []
    i = 0
    while i < n:
        if not voiced[i]:
            i += 1
            continue
        j, run = i, [midi[i]]
        while j + 1 < n and voiced[j + 1] and abs(midi[j + 1] - np.median(run[-8:])) < jump:
            j += 1
            run.append(midi[j])
        dur = (j - i + 1) * hop_s
        if dur >= min_dur:
            med = float(np.median(run))
            pitch = int(round(med))
            lv = float(np.max(level[i : j + 1]))
            vel = int(np.clip(round(127 * (1 - (loud_ref - lv) / 40.0)), 20, 127))
            out.append({"start": round(offset_s + i * hop_s, 3), "end": round(offset_s + (j + 1) * hop_s, 3), "pitch": pitch,
                        "cents": int(round((med - pitch) * 100)), "velocity": vel})
        i = j + 1
    return merge_repeats(out)


def merge_repeats(notes: list[dict], gap: float = 0.03) -> list[dict]:
    """Join a note to the previous one when it has the same pitch and starts within gap seconds (a frame dropout inside one sung note)."""
    out: list[dict] = []
    for nt in notes:
        if out and nt["pitch"] == out[-1]["pitch"] and nt["start"] - out[-1]["end"] <= gap:
            out[-1] = {**out[-1], "end": nt["end"], "velocity": max(out[-1]["velocity"], nt["velocity"])}
        else:
            out.append(dict(nt))
    return out


def key_from_notes(notes: list[dict]) -> dict:
    """{"tonic": pc, "mode": "major" or "minor", "name", "score", "runner_up"}: Krumhansl-Schmuckler on the duration-weighted pitch classes."""
    hist = np.zeros(12)
    for nt in notes:
        hist[nt["pitch"] % 12] += nt["end"] - nt["start"]
    if hist.sum() == 0:
        raise ValueError("no notes")
    rows = []
    for mode, prof in (("major", MAJOR), ("minor", MINOR)):
        for t in range(12):
            rows.append((float(np.corrcoef(hist, np.roll(prof, t))[0, 1]), t, mode))
    rows.sort(reverse=True)
    best, second = rows[0], rows[1]
    return {"tonic": best[1], "mode": best[2], "name": "%s %s" % (NAMES[best[1]], best[2]), "score": round(best[0], 3),
            "runner_up": "%s %s" % (NAMES[second[1]], second[2]), "margin": round(best[0] - second[0], 3)}


def to_beats(notes: list[dict], seconds_to_beat) -> list[dict]:
    """Notes with start and duration in beats (for write_midi_file) through a mapping function from seconds to beats."""
    out = []
    for nt in notes:
        a, b = seconds_to_beat(nt["start"]), seconds_to_beat(nt["end"])
        if b > a:
            out.append({"pitch": int(nt["pitch"]), "start": round(max(0.0, a), 4), "duration": round(b - a, 4), "velocity": int(nt["velocity"])})
    return out


def contour_similarity(a: list[dict], b: list[dict], step: float = 0.05) -> float:
    """How alike two melodies are, 0 to 1: the share of sampled times (every step seconds over the shorter span) where both sound the same
    pitch class, after the transposition that matches most. Robust to octave errors and to a remix sung in another key."""
    def grid(ns):
        if not ns:
            return np.array([]), 0.0
        t0 = ns[0]["start"]
        span = ns[-1]["end"] - t0
        g = np.full(int(span / step) + 1, -1)
        for nt in ns:
            g[int((nt["start"] - t0) / step) : int((nt["end"] - t0) / step)] = nt["pitch"] % 12
        return g, span
    ga, _ = grid(a)
    gb, _ = grid(b)
    m = min(len(ga), len(gb))
    if m == 0:
        return 0.0
    ga, gb = ga[:m], gb[:m]
    both = (ga >= 0) & (gb >= 0)
    either = (ga >= 0) | (gb >= 0)
    if not both.any():
        return 0.0
    agree = max(float(np.mean((ga[both] + k) % 12 == gb[both])) for k in range(12))  # best transposition
    return round(agree * both.sum() / either.sum(), 4)  # scaled by how much of the time both melodies sound
