"""Render an FX bed (impacts, air sweeps, risers, downlifters, sub drops, reverse cymbals, noise washes) from a cue list into one stereo array, with no ducking and no level moves.

Levels over time (fades, ducks under a vocal) belong to automation clips (coproducer.automation), not to the audio. Every cue is
{kind, bar, gain_db, ...}; positions are in bars of 4 beats. Rendering is deterministic.
"""
from __future__ import annotations

import numpy as np

from . import oneshots as O

SR = O.SR


def _db(x: float) -> float:
    return 10 ** (x / 20)


def cue_audio(c: dict, spb: float) -> tuple[float, np.ndarray]:
    """(start in beats, stereo audio) for one cue. spb is seconds per beat."""
    kind, bar, g = c["kind"], c["bar"], _db(c.get("gain_db", 0.0))
    t0 = bar * 4.0
    if kind == "impact":
        x = O.impact(length=c.get("seconds", 3.0))
        x = np.stack([x, np.roll(x, 25)], 1)
    elif kind == "air_sweep":
        beats = c.get("beats", 4)
        x = O.reverse_crash(beats * spb)
        x = O._hp(x, c.get("hp", 6000))
        t0 = bar * 4.0 + 4 - beats
    elif kind == "noise_riser":
        x = O.sweep_noise(c["bars"] * 4 * spb, c["f0"], c["f1"], c.get("power", 2.0))
    elif kind == "tone_riser":
        x = O.tone_riser(c["bars"] * 4 * spb, c["f0"], c["f1"], c.get("power", 2.0))
    elif kind == "downlifter":
        x = O.sweep_noise(c["beats"] * spb, c.get("f0", 400), c.get("f1", 9000))[::-1].copy()
    elif kind == "sub_drop":
        x = O.sub_drop(c.get("seconds", 2.0), c.get("f0", 62.0), c.get("f1", 31.0))
        x = np.stack([x, x], 1)
    elif kind == "reverse_cymbal":
        beats = c.get("beats", 4)
        x = O.reverse_crash(beats * spb)
        t0 = bar * 4.0 + 4 - beats
    elif kind == "noise_wash":
        x = O.noise_wash(c.get("bars", 2) * 4 * spb, c.get("f0", 1500), c.get("f1", 7000))
    elif kind == "reverse_sample":   # the record's own sound reversed into a downbeat (a held word, a strummed chord): no noise, no sweep (2026-11-02)
        beats = c.get("beats", 2)
        x = reversed_slice(c["path"], c["end_s"], beats * spb, c.get("hp", 120.0), c.get("lp", 6000.0))
        t0 = bar * 4.0 + 4 - beats
    else:
        raise ValueError("unknown FX cue kind %r" % kind)
    return t0, x * g


def reversed_slice(path: str, end_s: float, seconds: float, hp: float = 120.0, lp: float = 6000.0) -> np.ndarray:
    """The `seconds` of a file that end at end_s, reversed, band-limited, with a smooth swell in and a quick fade at its end, stereo at SR."""
    import soundfile as sf
    y, rate = sf.read(path, always_2d=True)
    m = y.mean(axis=1)
    a, b = max(0, int((end_s - seconds) * rate)), min(len(m), int(end_s * rate))
    seg = m[a:b][::-1].copy()
    if rate != SR:
        n = int(round(len(seg) * SR / rate))
        seg = np.interp(np.linspace(0, len(seg) - 1, max(n, 1)), np.arange(len(seg)), seg)
    seg = O._lp(O._hp(seg, hp), lp)
    n = len(seg)
    env = np.minimum(1.0, (np.arange(n) / max(n - 1, 1)) ** 1.5 * 1.1)
    tail = int(0.02 * SR)
    if tail and n > tail:
        env[-tail:] *= np.linspace(1.0, 0.0, tail)
    seg = seg * env
    peak = float(np.abs(seg).max()) or 1.0
    seg = seg / peak * 0.7
    return np.stack([seg, np.roll(seg, 40)], 1)


def render_bed(cues: list[dict], bpm: float, beats: float) -> np.ndarray:
    """Mix every cue into a float stereo array `beats` long. Cues past the end are cut."""
    spb = 60.0 / bpm
    out = np.zeros((int(round(beats * spb * SR)), 2))
    for c in cues:
        t0, x = cue_audio(c, spb)
        s = int(round(t0 * spb * SR))
        e = min(len(out), s + len(x))
        if s < len(out) and e > s:
            out[s:e] += x[: e - s]
    return out
