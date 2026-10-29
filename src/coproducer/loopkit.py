"""Clean loops, drum one-shots and patterns from a song's separated stems (skill loops-and-kits).

A stem separated from a finished mix carries bleed: the vocal in the drums, the kick in the bass. A loop that repeats in the song gets
cleaner when every repetition of it is aligned and averaged: what repeats adds up, what does not (a sung line, a fill, a crash) averages
out. The same holds for a drum hit: the median of every aligned kick on beats where nothing else plays is a clean kick, and a clap that
always lands on a kick is cleaned by subtracting that kick. Patterns come from the averaged step profile of three drum bands (kick below
110 Hz, snare or clap 1.2 to 4 kHz, hats above 7 kHz), bass notes from the averaged bass loop. Loops found elsewhere (FL's factory Packs)
are ranked against a song's patterns by the same step profiles. numpy, scipy, soundfile and mido only; the stems are only read.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy import signal

from . import bassnotes, dsp

STEPS = 16
BANDS = {"kick": (0.0, 110.0), "snare": (1200.0, 4000.0), "hat": (7000.0, 0.0)}   # 0 as the upper edge: a high-pass
VEL = {"X": 120, "x": 96, "o": 64}
GM = {"kick": 36, "snare": 38, "clap": 39, "hat": 42, "ohat": 46}


# ---- grid and bands

def bar_edges(bars: list[float], bpm: float, duration_s: float) -> np.ndarray:
    """The analysis grid's bar starts, extended by whole bars to the end of the audio, plus the end of the last bar."""
    edges = [float(b) for b in bars] or [0.0]
    bar = 240.0 / bpm
    while edges[-1] + bar <= duration_s + 1e-6:
        edges.append(edges[-1] + bar)
    return np.array(edges)


def regular_edges(bars: list[float], bpm: float, duration_s: float) -> np.ndarray:
    """Bar starts on an exact grid for a steady song: the bar length from the tempo, the offset fitted to the analysis grid (whose times are
    rounded to about 10 ms), extended over the whole audio. The first bar stays the grid's first bar, so bar numbers match the analysis.
    Loops cut on it are sample-exact lengths."""
    bar = 240.0 / bpm
    b = np.array([float(t) for t in bars]) if bars else np.array([0.0])
    k = np.round((b - b[0]) / bar)
    off = max(0.0, float(np.median(b - k * bar)))
    n = int((duration_s - off) / bar) + 1
    return np.array([off + i * bar for i in range(n + 1) if off + i * bar <= duration_s + 1e-6])


def _band(x: np.ndarray, rate: int, lo: float, hi: float) -> np.ndarray:
    nyq = rate / 2
    if lo <= 0:
        sos = signal.butter(4, min(hi, nyq * 0.95), btype="low", fs=rate, output="sos")
    elif hi <= 0 or hi >= nyq * 0.95:
        sos = signal.butter(4, lo, btype="high", fs=rate, output="sos")
    else:
        sos = signal.butter(4, [lo, hi], btype="band", fs=rate, output="sos")
    return signal.sosfilt(sos, x)


def _env(x: np.ndarray, rate: int, ms: float = 3.0) -> np.ndarray:
    n = max(1, int(rate * ms / 1000))
    return np.sqrt(np.convolve(x * x, np.ones(n) / n, mode="same") + 1e-18)


SMOOTH_MS = {"kick": 12.0, "snare": 4.0, "hat": 2.0}   # longer than a period of the band's lowest partials, or the envelope ripples
KICK_SHARE = 0.5         # a kick-band rise counts only when it is at least half the level it reaches: not a ringing body swelling again


def band_envelopes(x: np.ndarray, rate: int) -> dict:
    """{band: envelope} of a mono signal for the three drum bands."""
    return {k: _env(_band(x, rate, lo, hi), rate, SMOOTH_MS[k]) for k, (lo, hi) in BANDS.items()}


def profiles(envs: dict, rate: int, edges: np.ndarray, bars: list[int]) -> dict:
    """{band: step profile} for the three bands. In the kick band a rise must reach at least KICK_SHARE of the level it ends at: a layered
    kick whose body beats against itself, or a sub that swells, rises again a 16th later without being hit (an 808 with no click still
    counts: its rise starts from near silence)."""
    return {k: step_profile(envs[k], rate, edges, bars, min_share=KICK_SHARE if k == "kick" else 0.0) for k in BANDS}


def onsets(env: np.ndarray, rate: int, ms: float = 4.0) -> np.ndarray:
    """The rise of an envelope over ms (negative changes set to 0): where hits start, not how long they ring."""
    k = max(1, int(rate * ms / 1000))
    d = np.zeros_like(env)
    d[k:] = env[k:] - env[:-k]
    return np.maximum(d, 0.0)


def rise(env: np.ndarray, rate: int, ms: float = 25.0) -> np.ndarray:
    """How far the envelope stands above its lowest point in the ms before: large at a hit's attack, small where a sound rings on, beats
    or ripples."""
    from scipy.ndimage import minimum_filter1d
    n = max(1, int(rate * ms / 1000))
    centred = minimum_filter1d(env, size=n, mode="nearest")
    trailing = np.empty_like(env)
    h = n // 2
    trailing[h:] = centred[:len(env) - h]
    trailing[:h] = centred[0]
    return np.maximum(env - trailing, 0.0)


def step_profile(env: np.ndarray, rate: int, edges: np.ndarray, bars: list[int], steps: int = STEPS, attack: bool = True,
                 min_share: float = 0.0) -> np.ndarray:
    """The mean value at each step of the bar over the given 0-based bars: with attack (the default) the largest rise of the envelope
    (rise()) from 10 ms before the step to 60 % into it, so a kick ringing into the next 16th does not count as a second hit there; without,
    the envelope's peak in that window. min_share: a rise counts only when it is at least that share of the level it reaches (a hit starts
    from near silence or doubles what rings; a body that beats or swells again does not)."""
    src = rise(env, rate) if attack else env
    acc = np.zeros(steps)
    n = 0
    for b in bars:
        if b + 1 >= len(edges):
            continue
        a, z = edges[b], edges[b + 1]
        st = (z - a) / steps
        for s in range(steps):
            t = a + s * st
            i0, i1 = max(0, int((t - 0.01) * rate)), max(0, int((t + 0.6 * st) * rate))
            seg = src[i0:i1]
            if not len(seg):
                continue
            j = i0 + int(np.argmax(seg))
            if attack and min_share and float(seg.max()) < min_share * float(env[j]):
                continue
            acc[s] += float(seg.max())
        n += 1
    return acc / max(1, n)


def pattern(profile: np.ndarray, floor: float = 0.25) -> str:
    """A step string from a profile: X at 70 % of its loudest step or more, x at 40 %, o at the floor, . below."""
    top = float(profile.max()) or 1.0
    out = []
    for v in profile / top:
        out.append("X" if v >= 0.7 else "x" if v >= 0.4 else "o" if v >= floor else ".")
    return "".join(out)


def bar_vector(envs: dict, rate: int, edges: np.ndarray, bar: int) -> np.ndarray:
    """One bar's three step profiles side by side, each scaled to its own peak: the bar's drum pattern as a vector."""
    prof = profiles(envs, rate, edges, [bar])
    return np.concatenate([prof[k] / (prof[k].max() or 1.0) for k in BANDS])


def matching_bars(envs: dict, rate: int, edges: np.ndarray, bars: list[int], min_corr: float = 0.85) -> list[int]:
    """The bars whose drum pattern matches the median pattern of the set: fills, drop-outs and crashes left out."""
    vecs = {b: bar_vector(envs, rate, edges, b) for b in bars if b + 1 < len(edges)}
    if len(vecs) < 2:
        return list(vecs)
    med = np.median(np.array(list(vecs.values())), axis=0)
    return [b for b, v in vecs.items() if np.corrcoef(v, med)[0, 1] >= min_corr]


# ---- loops

def _segments(x: np.ndarray, rate: int, edges: np.ndarray, starts: list[int], n_bars: int) -> tuple[list[np.ndarray], int]:
    bar = float(np.median(np.diff(edges)))
    length = int(round(n_bars * bar * rate))
    segs = []
    for b in starts:
        i0 = int(round(edges[b] * rate))
        if i0 + length <= len(x):
            segs.append(x[i0:i0 + length])
    return segs, length


def _onset_env(x: np.ndarray, rate: int) -> np.ndarray:
    m = x if x.ndim == 1 else x.mean(axis=1)
    e = _env(m, rate, 2.0)
    return np.maximum(np.diff(e, prepend=e[0]), 0.0)


def average_loop(x: np.ndarray, rate: int, edges: np.ndarray, starts: list[int], n_bars: int, max_shift_ms: float = 12.0,
                 method: str = "median") -> tuple[np.ndarray, dict]:
    """The loop of n_bars that repeats from each start bar, every repetition aligned on the first by its onsets (within max_shift_ms) and
    then the median (or mean) of all of them. info: n (repetitions used), shifts_ms, residual_db (what was left out, the bleed, against the
    loop: lower is cleaner), corr (median correlation of a repetition with the loop)."""
    segs, length = _segments(x, rate, edges, starts, n_bars)
    if not segs:
        raise ValueError("no whole %d-bar repetition fits in the audio" % n_bars)
    ref = _onset_env(segs[0], rate)
    max_lag = int(rate * max_shift_ms / 1000)
    aligned, shifts = [segs[0]], [0.0]
    for s in segs[1:]:
        lag, _ = dsp.best_lag(ref, _onset_env(s, rate), max_lag)
        aligned.append(np.roll(s, -lag, axis=0))
        shifts.append(round(1000 * lag / rate, 2))
    stack = np.stack(aligned)
    loop = np.median(stack, axis=0) if method == "median" and len(aligned) > 2 else stack.mean(axis=0)
    res = [float(np.sqrt(np.mean((a - loop) ** 2))) for a in aligned]
    lvl = float(np.sqrt(np.mean(loop ** 2))) or 1e-12
    cor = [float(np.corrcoef(np.ravel(a), np.ravel(loop))[0, 1]) for a in aligned]
    return loop, {"n": len(aligned), "shifts_ms": shifts, "residual_db": round(20 * math.log10(max(np.median(res), 1e-12) / lvl), 1),
                  "corr": round(float(np.median(cor)), 3), "samples": length}


def loop_ends(loop: np.ndarray, rate: int, fade_ms: float = 3.0) -> np.ndarray:
    """A short fade at the loop's end only: a fade-in would soften the first kick."""
    y = loop.copy()
    k = min(len(y), int(rate * fade_ms / 1000))
    ramp = np.linspace(1.0, 0.0, k)
    y[-k:] = y[-k:] * (ramp[:, None] if y.ndim == 2 else ramp)
    return y


# ---- one-shots

def hit_times(env: np.ndarray, rate: int, edges: np.ndarray, bars: list[int], steps_hit: list[int], search_ms: float = 25.0) -> list[float]:
    """The time of the steepest rise of a band envelope near each grid step in steps_hit, bar by bar: the hit's attack."""
    out = []
    d = np.diff(env, prepend=env[0])
    w = int(rate * search_ms / 1000)
    for b in bars:
        if b + 1 >= len(edges):
            continue
        a, z = edges[b], edges[b + 1]
        for s in steps_hit:
            c = int((a + (z - a) * s / STEPS) * rate)
            lo, hi = max(0, c - w), min(len(d), c + w)
            if hi > lo:
                out.append((lo + int(np.argmax(d[lo:hi]))) / rate)
    return out


def average_hits(x: np.ndarray, rate: int, times: list[float], length_s: float, pre_s: float = 0.004, max_shift_ms: float = 3.0,
                 method: str = "median") -> tuple[np.ndarray, dict]:
    """A one-shot from many hits: each cut from pre_s before its attack for length_s, aligned on the first within max_shift_ms, then the
    median (or mean). info: n, residual_db (the bleed left out, against the shot), best (index of the single hit closest to the result)."""
    n, pre = int(length_s * rate), int(pre_s * rate)
    cuts = []
    for t in times:
        i0 = int(t * rate) - pre
        if i0 >= 0 and i0 + n <= len(x):
            cuts.append(x[i0:i0 + n])
    if not cuts:
        raise ValueError("no hit fits in the audio")
    max_lag = int(rate * max_shift_ms / 1000)
    ref = cuts[0] if cuts[0].ndim == 1 else cuts[0].mean(axis=1)
    aligned = [cuts[0]]
    for c in cuts[1:]:
        m = c if c.ndim == 1 else c.mean(axis=1)
        lag, _ = dsp.best_lag(ref, m, max_lag)
        aligned.append(np.roll(c, -lag, axis=0))
    stack = np.stack(aligned)
    shot = np.median(stack, axis=0) if method == "median" and len(aligned) > 2 else stack.mean(axis=0)
    res = [float(np.sqrt(np.mean((a - shot) ** 2))) for a in aligned]
    lvl = float(np.sqrt(np.mean(shot ** 2))) or 1e-12
    return shot, {"n": len(aligned), "residual_db": round(20 * math.log10(max(np.median(res), 1e-12) / lvl), 1), "best": int(np.argmin(res))}


def subtract(shot: np.ndarray, other: np.ndarray, rate: int, below_hz: float = 150.0, max_shift_ms: float = 6.0) -> tuple[np.ndarray, dict]:
    """shot minus other, aligned and scaled to cancel it below below_hz (least squares): a clap with the kick it always lands on taken out.
    Returns (result, {"gain", "shift_ms", "low_cut_db" (how far the low band fell)})."""
    n = min(len(shot), len(other))
    a = shot[:n]
    am = a if a.ndim == 1 else a.mean(axis=1)
    om = other[:n] if other.ndim == 1 else other[:n].mean(axis=1)
    la, lo = _band(am, rate, 0, below_hz), _band(om, rate, 0, below_hz)
    lag, _ = dsp.best_lag(la, lo, int(rate * max_shift_ms / 1000))   # positive: other's kick sits later than the shot's
    b = np.roll(other[:n], -lag, axis=0)
    lb = np.roll(lo, -lag)
    if lag > 0:
        b[-lag:] = 0.0
        lb[-lag:] = 0.0
    elif lag < 0:
        b[:-lag] = 0.0
        lb[:-lag] = 0.0
    g = max(0.0, min(2.0, float(np.dot(la, lb) / (np.dot(lb, lb) or 1.0))))
    out = shot.copy()
    out[:n] = a - g * b
    after = _band(out[:n] if out.ndim == 1 else out[:n].mean(axis=1), rate, 0, below_hz)
    cut = 10 * math.log10((float(np.dot(after, after)) + 1e-18) / (float(np.dot(la, la)) + 1e-18))
    return out, {"gain": round(g, 3), "shift_ms": round(1000 * lag / rate, 2), "low_cut_db": round(cut, 1)}


def lowpass_tail(shot: np.ndarray, rate: int, from_s: float, hz: float = 150.0, xfade_ms: float = 12.0) -> np.ndarray:
    """The shot with everything after from_s low-passed at hz (crossfaded over xfade_ms): a kick's long tail kept while the hat that played
    over it in the song is taken out."""
    i = int(from_s * rate)
    if i >= len(shot):
        return shot
    low = signal.sosfiltfilt(signal.butter(4, hz, btype="low", fs=rate, output="sos"), shot, axis=0)
    k = min(len(shot) - i, int(rate * xfade_ms / 1000))
    w = np.zeros(len(shot))
    w[i:i + k] = np.linspace(0.0, 1.0, k)
    w[i + k:] = 1.0
    w = w[:, None] if shot.ndim == 2 else w
    return shot * (1 - w) + low * w


def fade_tail(x: np.ndarray, rate: int, fade_ms: float = 10.0) -> np.ndarray:
    y = x.copy()
    k = min(len(y), int(rate * fade_ms / 1000))
    ramp = np.linspace(1.0, 0.0, k) ** 2
    y[-k:] = y[-k:] * (ramp[:, None] if y.ndim == 2 else ramp)
    return y


def shot_features(x: np.ndarray, rate: int) -> dict:
    """pitch_hz (the strongest partial from 30 to 200 Hz, 20 to 150 ms in: a kick's body), decay_ms (from the peak to 20 dB under it),
    centroid_hz (of the first 30 ms: the click)."""
    m = x if x.ndim == 1 else x.mean(axis=1)
    e = _env(m, rate, 2.0)
    pk = int(np.argmax(e))
    below = np.where(e[pk:] < e[pk] * 0.1)[0]
    decay = (below[0] if len(below) else len(e) - pk) / rate * 1000
    seg = m[int(0.02 * rate):int(0.15 * rate)]
    pitch = None
    if len(seg) > 256:
        f, p = signal.periodogram(seg * np.hanning(len(seg)), rate, nfft=1 << 15)
        sel = (f >= 30) & (f <= 200)
        if sel.any():
            pitch = round(float(f[sel][np.argmax(p[sel])]), 1)
    head = m[:int(0.03 * rate)]
    return {"pitch_hz": pitch, "decay_ms": round(float(decay), 1), "centroid_hz": round(dsp.spectral_centroid(head, rate), 0) if len(head) > 64 else None}


# ---- patterns and notes

def drum_patterns(envs: dict, rate: int, edges: np.ndarray, bars: list[int]) -> dict:
    """{band: step string} for a set of bars, and the raw profiles (for ranking loops)."""
    prof = profiles(envs, rate, edges, bars)
    return {"patterns": {k: pattern(v) for k, v in prof.items()}, "profiles": {k: [round(float(a), 6) for a in v] for k, v in prof.items()}}


def bass_notes(loop: np.ndarray, rate: int, bpm: float, steps_per_bar: int = STEPS) -> list[dict]:
    """The notes of a monophonic bass loop on the 16th grid: {step (from the loop start), steps (length), midi, cents}. Cleaned for a
    sidechained bass: a short blip at a note's start (the tracker locked onto a harmonic while the kick ducked the bass) joins the note it
    leads into (a fifth or an octave above it), a note split by a duck (the same pitch again within 45 ms) is one note, and a note far above
    the line folds down by octaves."""
    m = loop if loop.ndim == 1 else loop.mean(axis=1)
    t, midi, lvl = bassnotes.track_pitch(m, rate, fmin=25.0)
    raw = [dict(n) for n in bassnotes.notes_from_track(t, midi, lvl, min_len=0.04)]
    if not raw:
        return []
    joined: list[dict] = []
    for k, n in enumerate(raw):
        nxt = raw[k + 1] if k + 1 < len(raw) else None
        harmonic = nxt is not None and (n["pitch"] - nxt["pitch"]) % 12 in (0, 7) and n["pitch"] > nxt["pitch"]
        if harmonic and n["end"] - n["start"] < 0.12 and nxt["start"] - n["end"] < 0.02 and nxt["end"] - nxt["start"] > n["end"] - n["start"]:
            nxt["start"] = n["start"]          # an attack blip: the next note starts here
            continue
        joined.append(n)
    weight: dict = {}
    for n in joined:
        weight[n["pitch"]] = weight.get(n["pitch"], 0.0) + n["end"] - n["start"]
    main = max(weight, key=lambda k: weight[k])
    merged: list[dict] = []
    for n in joined:
        p = int(n["pitch"])
        while p - main > 14:
            p -= 12
        if merged and merged[-1]["midi"] == p and n["start"] - merged[-1]["end"] < 0.045:
            merged[-1]["end"] = n["end"]
            continue
        merged.append({"start": n["start"], "end": n["end"], "midi": p, "cents": n["cents"]})
    step_s = 60.0 / bpm / (steps_per_bar / 4)
    out: list[dict] = []
    for n in merged:
        s0 = int(round(n["start"] / step_s))
        if out and out[-1]["step"] >= s0:
            continue
        out.append({"step": s0, "steps": max(1, int(round((n["end"] - n["start"]) / step_s))), "midi": n["midi"], "cents": n["cents"]})
    return out


def write_midi(path: str | Path, tracks: dict, bpm: float, tpb: int = 96) -> Path:
    """A type 1 MIDI file: one track per name, notes (start_beat, dur_beats, key, velocity); drum tracks (name starting with "drums") on
    channel 10. FL imports it into the piano roll or the channel rack."""
    import mido
    f = mido.MidiFile(type=1, ticks_per_beat=tpb)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    f.tracks.append(meta)
    for name, notes in tracks.items():
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
        ch = 9 if name.startswith("drums") else 0
        ev = []
        for st, du, key, vel in notes:
            ev.append((int(round(st * tpb)), 1, key, vel))
            ev.append((int(round((st + du) * tpb)), 0, key, 0))
        ev.sort(key=lambda e: (e[0], e[1]))
        now = 0
        for tick, on, key, vel in ev:
            tr.append(mido.Message("note_on" if on else "note_off", note=int(key), velocity=int(vel), channel=ch, time=tick - now))
            now = tick
        f.tracks.append(tr)
    f.save(str(path))
    return Path(path)


def pattern_notes(pats: dict, bars: int = 1, voices: dict | None = None) -> list[tuple]:
    """(start_beat, dur, key, velocity) for step strings repeated over bars; voices maps a pattern name to a GM key."""
    keys = voices or GM
    out = []
    for name, pat in pats.items():
        if name not in keys:
            continue
        unit = 4.0 / len(pat)
        for b in range(bars):
            for i, c in enumerate(pat):
                if c in VEL:
                    out.append((b * 4 + i * unit, unit * 0.9, keys[name], VEL[c]))
    return out


# ---- finding loops

def loop_tempo(x: np.ndarray, rate: int, lo: float = 70.0, hi: float = 180.0) -> float:
    """A loop's tempo: a loop is a whole number of 4/4 bars (1, 2, 4, 8 or 16), so its length allows only a few tempos in lo to hi; the one
    the onset estimate (or a third or half of it either way) agrees with, else the one nearest 120."""
    dur = len(x) / rate
    allowed = [n * 240.0 / dur for n in (1, 2, 4, 8, 16) if lo <= n * 240.0 / dur <= hi]
    est = [c["bpm"] for c in dsp.estimate_tempo(x, rate, 60, 200)]
    if not allowed:
        return round(est[0], 2) if est else 120.0
    for e in est:
        for f in (1.0, 2.0, 0.5, 1.5, 2 / 3):
            hit = [b for b in allowed if abs(b - e * f) / b < 0.04]
            if hit:
                return round(hit[0], 2)
    return round(min(allowed, key=lambda b: abs(math.log(b / 120.0))), 2)


def describe_loop(x: np.ndarray, rate: int, bpm: float | None = None, max_bars: int = 4) -> dict:
    """A loop file read as drums: its tempo (given, or the best estimate from 70 to 180 bpm), bars, and the three step profiles over its
    first max_bars bars, assuming it starts on a downbeat (loops in packs do)."""
    m = x if x.ndim == 1 else x.mean(axis=1)
    dur = len(m) / rate
    if bpm is None:
        bpm = loop_tempo(x if x.ndim == 2 else m[:, None], rate)
    edges = bar_edges([0.0], bpm, dur)
    bars = list(range(min(max_bars, max(1, len(edges) - 1))))
    prof = profiles(band_envelopes(m, rate), rate, edges, bars)
    return {"bpm": bpm, "bars": round(dur * bpm / 240.0, 2), "seconds": round(dur, 2), "patterns": {k: pattern(v) for k, v in prof.items()},
            "profiles": {k: [round(float(a), 6) for a in v] for k, v in prof.items()}}


def similarity(a: dict, b: dict) -> float:
    """How alike two drum descriptions are (0 to 1): the mean cosine of their step profiles band by band, each band weighted by how much
    it plays in the target a."""
    tot, wsum = 0.0, 0.0
    for k in BANDS:
        pa, pb = np.array(a["profiles"][k], float), np.array(b["profiles"][k], float)
        if pa.max() <= 0:
            continue
        na, nb = pa / pa.max(), pb / (pb.max() or 1.0)
        cos = float(np.dot(na, nb) / ((np.linalg.norm(na) * np.linalg.norm(nb)) or 1.0))
        w = 1.0 if k != "kick" else 1.5
        tot += w * cos
        wsum += w
    return round(tot / (wsum or 1.0), 3)


def kick_distance(a: dict, b: dict) -> float:
    """A distance between two kicks' features: pitch in semitones, decay in octaves of time, click brightness in octaves."""
    d = 0.0
    if a.get("pitch_hz") and b.get("pitch_hz"):
        d += abs(12 * math.log2(a["pitch_hz"] / b["pitch_hz"])) / 3.0
    if a.get("decay_ms") and b.get("decay_ms"):
        d += abs(math.log2(a["decay_ms"] / b["decay_ms"]))
    if a.get("centroid_hz") and b.get("centroid_hz"):
        d += abs(math.log2(a["centroid_hz"] / b["centroid_hz"])) / 2.0
    return round(d, 3)
