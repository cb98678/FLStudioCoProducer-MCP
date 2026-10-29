"""Tune drum samples to the song's key with the channel pitch knob, as the Future House reference does (its three kicks sit 1 to 2 semitones down,
its claps, hats and crash up by 1 to 8).

A sample's pitch is read from its body: autocorrelation frames (bassnotes.track_pitch) after the first 30 ms whose level is within 20 dB of the
loudest, then the level-weighted median. The pitch FL plays adds the note the pattern uses most for that channel (a sampler plays its file as recorded
on C5, key 60, FL's default root) and the channel's pitch knob. The target is the nearest root or fifth of the key (or only the root), so with root
and fifth no sample moves more than 3.5 semitones. A sample with no clear pitch (a hat, a noisy clap) is left alone and reported.
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter

import numpy as np

from . import bassnotes, dsp, partmix
from .flpfile import Flp, FlpError

ROOT = 60
TARGETS = {"root": (0,), "root_fifth": (0, 7)}
FACTORY = "%FLStudioFactoryData%"


def key_pc(key: str) -> int:
    """Pitch class of a key name such as "A", "F#", "Bb minor" or "Am" (the mode does not change the root)."""
    m = re.match(r"\s*([A-Ga-g])([#b]?)", key or "")
    if not m:
        raise FlpError("unknown key %r (use a note name such as A, F# or Bb)" % key)
    name = m.group(1).upper() + m.group(2)
    name = {"Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#", "Ab": "G#", "Bb": "A#", "Cb": "B", "E#": "F", "B#": "C"}.get(name, name)
    return bassnotes.NAMES.index(name)


def sample_pitch(x: np.ndarray, rate: int, fmax: float = 260.0) -> float | None:
    """MIDI pitch (fractional) of a one-shot's body, or None when it has no clear pitch: fewer than 3 pitched frames, fewer than a third of
    its loud frames pitched, or pitched frames that spread over more than a semitone (noise reads as scattered pitches)."""
    t, midi, level = bassnotes.track_pitch(dsp.mono(x) if x.ndim > 1 else x, rate, hop_s=0.005, fmin=30.0, fmax=fmax)
    loud = (t > 0.03) & (level >= level.max() * 0.1 if len(level) else False)
    keep = loud & ~np.isnan(midi)
    if keep.sum() < 3 or keep.sum() < loud.sum() / 3:
        return None
    m, w = midi[keep], level[keep]
    q1, q3 = np.percentile(m, [25, 75])
    if q3 - q1 > 1.0:
        return None
    order = np.argsort(m)
    cum = np.cumsum(w[order])
    rough = float(m[order][np.searchsorted(cum, cum[-1] / 2)])
    return _refine(x if x.ndim == 1 else dsp.mono(x), rate, t[keep][0], t[keep][-1], rough, fmax)


def _refine(x: np.ndarray, rate: int, t0: float, t1: float, rough: float, fmax: float = 1e9) -> float:
    """The strongest spectral peak within 3 semitones of the rough pitch, over the pitched part (zero-padded FFT): autocorrelation on a decaying
    tone reads about a quarter tone sharp."""
    seg = x[int(max(0.0, t0 - 0.04) * rate) : int((t1 + 0.04) * rate)]
    if len(seg) < rate // 50:
        return rough
    n = 1 << max(18, int(len(seg)).bit_length() + 2)
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
    hz = np.fft.rfftfreq(n, 1.0 / rate)
    f0 = 440 * 2 ** ((rough - 69) / 12)
    band = (hz > f0 * 2 ** (-3 / 12)) & (hz < min(f0 * 2 ** (3 / 12), fmax))
    if not band.any():
        return rough
    peak = hz[band][int(np.argmax(spec[band]))]
    return float(69 + 12 * np.log2(peak / 440.0))


def default_channels(f: Flp) -> list[int]:
    """Sampler channels worth tuning: kicks, toms and 808s (the parts with a clear low pitch)."""
    out = []
    for ch in f.channel_ids():
        info = f.channel_info(ch)
        words = (info["name"] or "").lower().replace("_", " ").split()
        if info["sample"] and (partmix.role_of(info["name"] or "") == "kick" or any(w.startswith(("tom", "808")) for w in words)):
            out.append(ch)
    return out


def played_key(f: Flp, ch: int) -> int:
    """The note the patterns use most for channel ch (or for a Layer channel that plays it), else C5."""
    parents = [c for c in f.channel_ids() if ch in f.layer_children(c)]
    keys = Counter(n[2] for ns in f.pattern_notes().values() for n in ns if n[1] == ch or n[1] in parents)
    return keys.most_common(1)[0][0] if keys else ROOT


def nearest(midi: float, pcs: tuple, tonic: int) -> int:
    best = None
    for pc in pcs:
        target_pc = (tonic + pc) % 12
        base = round(midi) - ((round(midi) - target_pc) % 12)
        for m in (base, base + 12):
            if best is None or abs(m - midi) < abs(best - midi):
                best = m
    return best


def host_path(path: str, fl_exe: str | None) -> str:
    """A sample path as this computer sees it: FL's %FLStudioFactoryData% is FL's install folder."""
    if path.startswith(FACTORY):
        if not fl_exe:
            return ""
        return os.path.dirname(fl_exe) + path[len(FACTORY):]
    return path


def fmax_for(name: str) -> float:
    """Highest body pitch to look for: a kick's or an 808's body sits below about 160 Hz (above that is its click or a top layer); a tom's below 400 Hz."""
    low = partmix.role_of(name) == "kick" or "808" in name
    return 160.0 if low else 400.0


def plan(f: Flp, channels: list[int], key: str, targets: str = "root_fifth", fl_exe: str | None = None, fmax: float | None = None) -> list[dict]:
    """Per channel: its sample, the pitch it plays now, the target and the new pitch knob value in cents (None when it is left alone, with a reason)."""
    tonic, pcs = key_pc(key), TARGETS[targets]
    rows = []
    for ch in channels:
        info = f.channel_info(ch)
        row = {"channel": ch, "name": info["name"], "sample": info["sample"], "cents": None}
        cents, _rng = f.channel_pitch(ch)
        path = host_path(info["sample"] or "", fl_exe)
        if not path or not os.path.isfile(path):
            rows.append(dict(row, reason="sample file not found"))
            continue
        x, rate = dsp.load_audio(path, max_seconds=3.0)
        p = sample_pitch(x, rate, fmax or fmax_for(info["name"] or ""))
        if p is None:
            rows.append(dict(row, reason="no clear pitch"))
            continue
        offset = played_key(f, ch) - ROOT
        now = p + offset + cents / 100.0
        target = nearest(now, pcs, tonic)
        new = int(round((target - p - offset) * 100))
        rows.append(dict(row, hz=round(440 * 2 ** ((p - 69) / 12), 1), sample_note=_name(p), now_note=_name(now), target_note=_name(target),
                         old_cents=cents, cents=new))
    return rows


def _name(m: float) -> str:
    n = int(round(m))
    return "%s%d%+d" % (bassnotes.NAMES[n % 12], n // 12, int(round((m - n) * 100))) if not math.isnan(m) else "?"


def apply(f: Flp, rows: list[dict]) -> int:
    done = 0
    for r in rows:
        if r.get("cents") is not None:
            f.set_channel_pitch(r["channel"], r["cents"])
            done += 1
    return done
