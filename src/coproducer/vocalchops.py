"""Find phrases and syllable-sized chop points in a vocal stem. numpy and scipy only; no lyrics, only energy and onsets."""
from __future__ import annotations

import itertools

import numpy as np
from scipy import signal


def envelope_db(x: np.ndarray, rate: int, win_s: float = 0.02) -> tuple[np.ndarray, float]:
    """RMS envelope in dB re full scale per window; returns (env_db, window_seconds)."""
    n = max(1, int(win_s * rate))
    m = len(x) // n
    frames = x[: m * n].reshape(m, n)
    rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-14)
    return 20 * np.log10(rms), n / rate


def phrases(x: np.ndarray, rate: int, gate_db: float = -40.0, min_gap: float = 0.28, min_len: float = 0.3) -> list[dict]:
    """Voiced stretches {start, end, level_db}: above gate_db relative to the loud 95th percentile, gaps shorter than min_gap bridged."""
    env, w = envelope_db(x, rate)
    peak = float(np.percentile(env, 95))
    on = env > max(peak + gate_db, -70.0)
    idx = np.flatnonzero(on)
    if len(idx) == 0:
        return []
    out: list[list[int]] = []
    s = p = int(idx[0])
    gap = int(min_gap / w)
    for i in idx[1:]:
        if i - p > gap:
            out.append([s, p])
            s = int(i)
        p = int(i)
    out.append([s, p])
    res = []
    for a, b in out:
        if (b - a + 1) * w >= min_len:
            res.append({"start": round(a * w, 3), "end": round((b + 1) * w, 3), "level_db": round(float(np.mean(env[a : b + 1])), 1)})
    return res


def onsets(x: np.ndarray, rate: int, t0: float, t1: float, min_gap: float = 0.09) -> list[float]:
    """Syllable onset times inside [t0, t1): peaks of the rising 300 to 4000 Hz energy, at least min_gap apart."""
    seg = x[int(t0 * rate) : int(t1 * rate)]
    if len(seg) < 2048:
        return []
    f, t, z = signal.stft(seg, rate, nperseg=1024, noverlap=1024 - 256, boundary=None)
    band = (f >= 300) & (f <= 4000)
    e = np.log1p(30 * np.abs(z[band]).sum(axis=0))
    flux = np.maximum(np.diff(e), 0)
    if flux.max() <= 0:
        return []
    hop = t[1] - t[0]
    pk, _ = signal.find_peaks(flux, height=0.25 * flux.max(), distance=max(1, int(min_gap / hop)))
    return [round(t0 + float(t[p + 1]), 3) for p in pk]


def chop_candidates(x: np.ndarray, rate: int, ph: list[dict], min_len: float = 0.12, max_len: float = 0.7) -> list[dict]:
    """Syllable-sized slices {start, end, level_db} between successive onsets inside each phrase (a phrase start counts as an onset)."""
    out = []
    for p in ph:
        marks = [p["start"]] + [o for o in onsets(x, rate, p["start"], p["end"]) if o > p["start"] + 0.05] + [p["end"]]
        for a, b in itertools.pairwise(marks):
            if min_len <= b - a <= max_len:
                seg = x[int(a * rate) : int(b * rate)]
                out.append({"start": round(a, 3), "end": round(b, 3), "level_db": round(20 * float(np.log10(np.sqrt(np.mean(seg**2)) + 1e-9)), 1)})
    return out


# ---- finding where a sung word or phrase really starts and ends
#
# Whisper word times drift by 0.2 to 0.7 s on sung vocals, and snapping a cut to the nearest energy minimum lands inside held vowels (a cut of "my blues away"
# ended inside "away" for that reason). The cut points below come from the signal: a start is a syllable onset, an end is where the voice drops into a gap or
# silence, and the Whisper time is only a hint of where to look.

def hf_db(x: np.ndarray, rate: int, win_s: float = 0.01) -> np.ndarray:
    """Level of the 4 to 12 kHz band per window, where sibilants (the s of "places" or "drowns") live; a sung s is 10 to 25 dB below the vowel but is not silence."""
    hi = min(12000.0, 0.45 * rate)
    sos = signal.butter(4, [min(4000.0, 0.4 * hi), hi], btype="band", fs=rate, output="sos")
    return envelope_db(signal.sosfilt(sos, x), rate, win_s)[0]


def pitch_track(x: np.ndarray, rate: int, t0: float, t1: float, hop_s: float = 0.01, win_s: float = 0.046, fmin: float = 80.0, fmax: float = 800.0,
                gate_db: float = -45.0, clarity: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """(times, f0 in Hz with nan where unvoiced) from t0 to t1: normalised autocorrelation per window, the shortest lag within 90% of the best
    peak (so a sub-octave is not taken for the note), voiced when that peak is at least `clarity` and the window is above gate_db."""
    n, h = int(win_s * rate), max(1, int(hop_s * rate))
    lo, hi = int(rate / fmax), int(rate / fmin)
    a, b = max(0, int(t0 * rate)), min(len(x), int(t1 * rate))
    times, f0 = [], []
    for i in range(a, max(a, b - n), h):
        fr = x[i:i + n].astype(np.float64)
        fr = fr - fr.mean()
        times.append((i + n / 2) / rate)
        e = float(np.dot(fr, fr))
        if e <= 0 or 10 * np.log10(e / n + 1e-14) < gate_db:
            f0.append(np.nan)
            continue
        spec = np.fft.rfft(fr, 2 * n)
        ac = np.fft.irfft(spec * np.conj(spec))[: n]
        ac = ac / (ac[0] + 1e-12)
        seg = ac[lo:min(hi, n - 1)]
        if len(seg) == 0 or seg.max() < clarity:
            f0.append(np.nan)
            continue
        k = int(np.argmax(seg >= 0.9 * seg.max()))           # the first peak region within 90% of the best: the note, not a sub-octave
        while k + 1 < len(seg) and seg[k + 1] >= seg[k]:
            k += 1                                             # climb to that region's own peak
        d = 0.0
        if 0 < k < len(seg) - 1:                              # parabolic interpolation between lags
            y0, y1, y2 = seg[k - 1], seg[k], seg[k + 1]
            den = y0 - 2 * y1 + y2
            d = 0.5 * (y0 - y2) / den if den else 0.0
        f0.append(rate / (lo + k + d))
    return np.array(times), np.array(f0)


def gaps(x: np.ndarray, rate: int, depth_db: float = 12.0, around_s: float = 0.6, min_len: float = 0.08, close_s: float = 0.06, floor_db: float = -50.0,
         hf_guard: bool = True, hf_floor_db: float = -47.0) -> list[tuple[float, float]]:
    """Stretches (start, end) where the voice is silent or at least depth_db below the loudest point within around_s, lasting min_len or more.

    Holes shorter than close_s inside a stretch are bridged, so a single loud frame inside a breath does not split it. With hf_guard a frame only counts as quiet if
    the 4 to 12 kHz band is quiet too (below hf_floor_db, or depth_db below its own local maximum): a trailing s or f is faint overall but is not a gap, and ending a
    cut at the dip before it clips the word ("places" read as "place").
    """
    env, w = envelope_db(x, rate, 0.01)
    k = max(1, int(around_s / w))

    def local_max(e: np.ndarray) -> np.ndarray:
        pad = np.pad(e, k, mode="edge")
        return np.array([pad[i : i + 2 * k + 1].max() for i in range(len(e))])

    low = (env < local_max(env) - depth_db) | (env < floor_db)
    close = max(1, int(close_s / w))
    idx = np.flatnonzero(low)
    out: list[tuple[int, int]] = []
    if len(idx):
        s = p = int(idx[0])
        for i in idx[1:]:
            if i - p > close:
                out.append((s, p))
                s = int(i)
            p = int(i)
        out.append((s, p))
    if hf_guard and out:
        # A gap that opens with a hiss is not yet a gap: move its start past the hiss. Only the start moves, since a stop closure ("whis-KEY") is silent in every band.
        h = hf_db(x, rate, 0.01)[: len(env)]
        h = np.pad(h, (0, len(env) - len(h)), mode="edge")
        hissy = (h > hf_floor_db) & (h > local_max(h) - 2 * depth_db)
        moved = []
        for a, b in out:
            while a <= b and hissy[a]:
                a += 1
            moved.append((a, b))
        out = moved
    return [(round(a * w, 3), round((b + 1) * w, 3)) for a, b in out if (b - a + 1) * w >= min_len]


def snap_start(ons: list[float], hint: float, before: float = 0.3, after: float = 0.25, preroll: float = 0.02) -> float:
    """The syllable onset nearest the hint (looking back before and ahead after seconds), minus a short pre-roll so the attack is whole. Hint if none."""
    cand = [o for o in ons if hint - before <= o <= hint + after]
    if not cand:
        return hint
    return min(cand, key=lambda o: abs(o - hint)) - preroll


def snap_end(ons: list[float], gp: list[tuple[float, float]], hint: float, mode: str = "word", tail: float = 0.03, preroll: float = 0.02, reach: float = 0.25) -> float:
    """Where a cut that should end near hint really ends.

    "phrase": the start of the first gap (or silence) after the hint, plus a short tail, so a held last word such as "away" keeps its whole vowel.
    "word": the nearest onset within reach of the hint (minus the pre-roll, so the next word does not leak in), unless a gap begins sooner.
    """
    after = [g for g in gp if g[1] > hint]
    first_gap = after[0][0] if after else None
    if first_gap is not None and first_gap < hint:  # the hint sits inside a gap already
        return first_gap + tail
    if mode == "phrase":
        return (first_gap + tail) if first_gap is not None else hint
    cand = [o for o in ons if hint - reach <= o <= hint + reach]
    end = (min(cand, key=lambda o: abs(o - hint)) - preroll) if cand else hint
    if first_gap is not None and first_gap < end:
        end = first_gap + tail
    return end


def squeeze_gaps(x: np.ndarray, rate: int, gp: list[tuple[float, float]], max_gap: float, fade: float = 0.015) -> np.ndarray:
    """Remove the middle of every gap longer than max_gap, keeping max_gap / 2 of quiet on each side with a short crossfade, so a chop of two phrases stays tight."""
    segs, cursor = [], 0
    for g0, g1 in gp:
        if g1 - g0 > max_gap:
            a = int((g0 + max_gap / 2) * rate)
            b = int((g1 - max_gap / 2) * rate)
            segs.append((cursor, a))
            cursor = b
    segs.append((cursor, len(x)))
    n = max(1, int(fade * rate))
    out = np.zeros((0,) + x.shape[1:], dtype=x.dtype)
    for i, (a, b) in enumerate(segs):
        part = x[a:b].copy()
        if i:
            ramp = np.linspace(0, 1, min(n, len(part)))
            part[: len(ramp)] *= ramp.reshape((-1,) + (1,) * (x.ndim - 1))
        if i < len(segs) - 1:
            ramp = np.linspace(1, 0, min(n, len(part)))
            part[-len(ramp) :] *= ramp.reshape((-1,) + (1,) * (x.ndim - 1))
        out = np.concatenate([out, part])
    return out


def cut_report(x: np.ndarray, rate: int, start: float, end: float) -> dict:
    """Checks on a cut: level at each edge relative to the loudest point inside it (a good cut starts after a rise and ends 20 dB or more down)."""
    env, w = envelope_db(x[int(start * rate) : int(end * rate)], rate, 0.01)
    if len(env) < 4:
        return {"ok": False, "reason": "too short"}
    peak = float(env.max())
    head, tail = float(env[:3].mean()) - peak, float(env[-3:].mean()) - peak
    return {"ok": tail <= -18.0, "start_rel_db": round(head, 1), "end_rel_db": round(tail, 1), "length_s": round(end - start, 3)}
