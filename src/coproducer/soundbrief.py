"""How a part of the original record sounds, measured, so the remix's own synth sounds can be designed to belong to it (2026-10-26).

The person: "we try to generate our own sounds that sonically match the original song. Same tone, key, attack, decay ... we try to
musically match what exists and then do interesting and unique things." So before a Serum 2 sound is generated, the part it answers
is read from its stem: the notes' amplitude envelope (attack, hold, decay, sustain, release), the brightness and how it moves inside a
note, the harmonic series of the clearest notes (which harmonics lead, how fast they fall), noise and grit, stereo width and register.

describe() returns those numbers with the words a sound designer would use; starting_point() turns them into a first draft for the
serum-mcp server (an oscillator whose custom wavetable is the measured harmonics, the measured envelope, unison from the width);
compare() measures a remake against the original and says what to change. The draft is where the design starts, not where it ends:
the surprise and the taste are decided by ear, and every number here is a measurement of one stem with its separation artefacts.
"""
from __future__ import annotations

import math

import numpy as np

HOP_S = 0.005
FLOOR_DB = -60.0
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
# serum-mcp's own calibration of its filter cutoff value against the 85% rolloff of filtered white noise (its docs/PARAMETER_SCHEMA.md,
# "Filter cutoff Hz curve", calibrated 2026-07-31). Used only to suggest a starting cutoff.
SERUM_CUTOFF_ROLLOFF = ((0.05, 21.5), (0.15, 43.1), (0.25, 64.6), (0.35, 129.2), (0.45, 323.0), (0.55, 710.6), (0.65, 1571.9),
                        (0.75, 3466.8), (0.85, 7558.2), (0.95, 12919.9), (1.0, 14427.2))
ATTACK_ABS_S = 0.004   # attacks closer than 4 ms are the same attack to the reading (1 ms steps, a window of one and a half periods)
# How far a remake may sit from the original before compare() asks for a change.
TOL = {"attack_ratio": 0.5, "decay_ratio": 0.35, "sustain": 0.15, "release_ratio": 0.5, "centroid_ratio": 0.25, "slope_db": 3.0, "gated_share": 0.4,
       "odd_even_db": 6.0, "width_db": 6.0, "register_semitones": 7.0}


def load_slice(path: str, start_s: float = 0.0, end_s: float = 0.0) -> tuple[np.ndarray, int]:
    """(samples, channels) float64 and the rate, from start_s to end_s (0 = to the end). Raises ValueError when unreadable or empty."""
    import soundfile as sf
    try:
        rate = int(sf.info(path).samplerate)
        stop = int(end_s * rate) if end_s > 0 else None
        x, _ = sf.read(path, start=int(max(0.0, start_s) * rate), stop=stop, dtype="float64", always_2d=True)
    except (RuntimeError, OSError) as e:
        raise ValueError("cannot read audio file: %s" % e) from e
    if len(x) < rate // 10:
        raise ValueError("less than 0.1 s of audio in that stretch")
    return x, rate


def _db(x):
    return 20.0 * np.log10(np.maximum(x, 1e-9))


def envelope(m: np.ndarray, rate: int, hop_s: float = HOP_S, win_s: float = 0.02) -> np.ndarray:
    """RMS level per hop (linear) over a sliding window centred on the hop. 20 ms is longer than a bass note's period, so the level
    does not ripple with the waveform; the attack is measured separately on a finer window (fine_attack)."""
    h, n = max(1, int(hop_s * rate)), max(1, int(win_s * rate))
    if len(m) < n:
        return np.zeros(0)
    c = np.concatenate([[0.0], np.cumsum(m.astype(np.float64) ** 2)])
    rms = np.sqrt(np.maximum(c[n:] - c[:-n], 0.0) / n)
    pad = np.concatenate([np.full(n // 2, rms[0]), rms, np.full(n - n // 2 - 1, rms[-1])])
    return pad[::h]


def note_segments(env: np.ndarray, hop_s: float = HOP_S, rise_db: float = 8.0, min_gap_s: float = 0.08, floor_db: float = -50.0,
                  rise_s: float = 0.03) -> list[tuple]:
    """(start, end) hop indexes of the notes: a rise of rise_db within rise_s (30 ms) marks an onset (the frame at the bottom of the rise);
    a note runs to the next onset, or until it falls 45 dB below its peak."""
    e = _db(env)
    top = float(e.max()) if len(e) else FLOOR_DB
    w = max(2, int(rise_s / hop_s))
    gap = max(1, int(min_gap_s / hop_s))
    starts: list[int] = []
    for i in range(w, len(e)):
        lo = int(np.argmin(e[i - w:i])) + i - w
        if e[i] - e[lo] >= rise_db and e[i] > top + floor_db and (not starts or lo - starts[-1] >= gap):
            starts.append(lo)
    out = []
    for k, s0 in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(e)
        pk = s0 + int(np.argmax(e[s0:end]))
        quiet = np.where(e[pk:end] < e[pk] - 45.0)[0]
        out.append((s0, pk + int(quiet[0]) if len(quiet) else end))
    return out


def held_segments(env: np.ndarray, hop_s: float = HOP_S, floor_db: float = -50.0) -> list[tuple]:
    """Notes of a sound with no fast onset: a pad swelling in over half a second, or a legato sub or drone already sounding when the
    slice begins (2026-10-28: the demo solos of a FLEX drone and a 3x Osc sub read as no notes). Slow rises first; else the whole
    stretch above the floor is one note."""
    segs = note_segments(env, hop_s, rise_s=0.5)
    if segs:
        return segs
    e = _db(env)
    if not len(e) or float(e.max()) < -80.0:   # digital silence or a noise floor is not a held note
        return []
    on = np.where(e > float(e.max()) + floor_db)[0]
    return [(int(on[0]), int(on[-1]) + 1)] if len(on) >= max(2, int(0.15 / hop_s)) else []


def _slope_db_per_s(seg: np.ndarray, hop_s: float) -> float:
    t = np.arange(len(seg)) * hop_s
    return float(np.polyfit(t, _db(seg), 1)[0]) if len(seg) >= 4 else 0.0


def plateau(tail_db: np.ndarray, hop_s: float, flat_db_per_s: float = 6.0) -> tuple[int, int] | None:
    """The longest stretch after the peak where the level holds (falls or rises less than flat_db_per_s over 50 ms windows), when it
    lasts at least 0.15 s and a fifth of the note: the sustain. None for a sound that keeps falling (a pluck, a piano)."""
    w = max(2, int(0.05 / hop_s))
    if len(tail_db) < 2 * w:
        return None
    smooth = np.convolve(tail_db, np.ones(w) / w, mode="valid")
    rate = np.abs(smooth[w:] - smooth[:-w]) / (w * hop_s)
    flat = np.concatenate([rate < flat_db_per_s, [False]])
    best, run0 = None, None
    for i, f in enumerate(flat):
        if f and run0 is None:
            run0 = i
        elif not f and run0 is not None:
            if best is None or i - run0 > best[1] - best[0]:
                best = (run0, i)
            run0 = None
    if best is None or (best[1] - best[0]) * hop_s < max(0.15, 0.2 * len(tail_db) * hop_s):
        return None
    return best[0] + w // 2, best[1] + w + w // 2


def gate_point(tail_db: np.ndarray, hop_s: float, fall_db_per_s: float = 200.0) -> int | None:
    """Where a note is cut off (a note-off with a short release, or a gate): the level falls 20 dB below the peak and the last 30 ms
    before that fell faster than fall_db_per_s. Returns the index where the cut starts, or None for a note that dies away by itself."""
    below = np.where(tail_db <= tail_db[0] - 20.0)[0]
    w = max(2, int(0.03 / hop_s))
    if not len(below) or below[0] <= w:
        return None
    i = int(below[0])
    return i - w if (tail_db[i - w] - tail_db[i]) / (w * hop_s) > fall_db_per_s else None


def note_envelope(env: np.ndarray, s0: int, s1: int, hop_s: float = HOP_S, next_onset: int | None = None) -> dict:
    """Attack (10 to 90 %), hold, decay, sustain (0 to 1 of the peak) and release of one note, in seconds (resolution one hop, 5 ms).
    A note that is cut off (staccato, gated) is told apart from one that dies away: its decay and sustain come from the part before the
    cut and its release from the cut itself, so short bass notes are not read as a plucked patch."""
    seg = env[s0:s1]
    pk = int(np.argmax(seg))
    peak = float(seg[pk]) or 1e-9
    t10 = int(np.argmax(seg >= 0.1 * peak))
    t90 = int(np.argmax(seg >= 0.9 * peak))
    above = seg[t90:] >= 0.9 * peak
    hold = int(np.argmin(above)) if not above.all() else len(above)
    tail = seg[pk:]
    td = _db(tail)
    cut = gate_point(td, hop_s)
    held = tail[:cut] if cut else tail
    flat = plateau(_db(held), hop_s) if not cut else ((len(held) // 2, len(held)) if len(held) * hop_s >= 0.04 else None)
    sus = float(np.median(held[flat[0]:flat[1]]) / peak) if flat else 0.0
    if flat and sus < 10 ** (-35 / 20):
        flat, sus = None, 0.0                                   # a held level 35 dB down is a tail, not a sustain
    goal = sus + 0.1 * (1.0 - sus) if flat else 0.1
    reach = np.where(held <= goal * peak)[0]
    if len(reach):
        decay = float(reach[0] * hop_s)
    elif cut:
        decay = float(len(held) * hop_s)
    else:                                                      # still falling at the end of the note: extrapolate the fall to -20 dB
        slope = _slope_db_per_s(tail[int(len(tail) * 0.6):], hop_s)
        drop = float(td[0] - td[-1])
        decay = len(tail) * hop_s + max(0.0, 20.0 - drop) / max(abs(slope), 1.0) if slope < -1.0 else len(tail) * hop_s
    release = None
    if flat and (cut or next_onset is None or next_onset - s1 > int(0.3 / hop_s)):
        off = pk + (cut if cut else flat[1])
        fall = np.where(seg[off:] <= max(sus, 0.05) * peak * 10 ** (-30 / 20))[0]
        release = float(fall[0] * hop_s) if len(fall) else None
    return {"attack_s": round(max(t90 - t10, 1) * hop_s, 4), "hold_s": round(hold * hop_s, 4), "decay_s": round(decay, 3),
            "sustain": round(min(1.0, sus), 3), "release_s": None if release is None else round(release, 3), "gated": cut is not None,
            "length_s": round((s1 - s0) * hop_s, 3), "peak_db": round(float(td[0]), 1)}


def fine_attack(m: np.ndarray, rate: int, t0: float, t1: float, f0: float | None) -> float | None:
    """t0: the note's start; t1: where the coarse level first comes within 2 dB of the note's peak (the end of the rise)."""
    """Attack time (10 to 90 % of the rise) on a sliding RMS one and a half periods long (5 ms at least, 20 ms without a pitch), stepped
    every millisecond, with the window's own rise taken out. Low notes need the longer window or their ripple reads as a slow attack."""
    w = max(0.005, 1.5 / f0) if f0 else 0.02
    a, b = max(0, int((t0 - w) * rate)), min(len(m), int(t1 * rate))
    x = m[a:b] ** 2
    n = max(1, int(w * rate))
    if len(x) <= n + 2:
        return None
    c = np.concatenate([[0.0], np.cumsum(x)])
    rms = np.sqrt((c[n:] - c[:-n]) / n)[:: max(1, rate // 1000)]
    top = int(np.argmax(rms))
    pk = float(rms[top]) or 1e-12
    lo_i = int(np.argmin(rms[: top + 1]))
    lo = float(rms[lo_i])                                      # the floor the note rises from (the last note may still ring)
    i10 = lo_i + int(np.argmax(rms[lo_i: top + 1] >= lo + 0.1 * (pk - lo)))
    i90 = lo_i + int(np.argmax(rms[lo_i: top + 1] >= lo + 0.9 * (pk - lo)))
    raw = (i90 - i10) / 1000.0
    return round(float(np.sqrt(max(raw ** 2 - (0.8 * w) ** 2, 0.0))) or 0.001, 4)


def yin_f0(x: np.ndarray, rate: int, fmin: float = 30.0, fmax: float = 2000.0, threshold: float = 0.15) -> float | None:
    """Fundamental of one frame by YIN (de Cheveigne and Kawahara 2002: cumulative mean normalised difference, first dip under the
    threshold, parabolic interpolation). None when the frame has no clear period. The frame must hold two periods of fmin."""
    w = len(x) // 2
    tmax, tmin = min(int(rate / fmin), w - 1), max(2, int(rate / fmax))
    if tmax <= tmin + 2:
        return None
    x = x - x.mean()
    n = 1 << int(np.ceil(np.log2(2 * len(x))))
    fx = np.fft.rfft(x, n)
    r = np.fft.irfft(np.fft.rfft(x[:w][::-1], n) * fx, n)[w - 1: w - 1 + tmax + 1]      # r[t] = sum x[j] x[j+t], j < w
    c = np.concatenate([[0.0], np.cumsum(x ** 2)])
    e0 = c[w]
    et = c[np.arange(tmax + 1) + w] - c[np.arange(tmax + 1)]
    d = e0 + et - 2 * r
    d[0] = 0.0
    cm = np.ones_like(d)
    cs = np.cumsum(d[1:])
    cm[1:] = d[1:] * np.arange(1, tmax + 1) / np.maximum(cs, 1e-12)
    below = np.where(cm[tmin:] < threshold)[0]
    if len(below):
        k = tmin + int(below[0])
        while k + 1 <= tmax and cm[k + 1] < cm[k]:
            k += 1
    else:
        k = tmin + int(np.argmin(cm[tmin:]))
        if cm[k] > 0.25:                                       # no clear period: noise, or several notes at once
            return None
    dd = 0.0
    if 0 < k < tmax:
        y0, y1, y2 = cm[k - 1], cm[k], cm[k + 1]
        den = y0 - 2 * y1 + y2
        dd = 0.5 * (y0 - y2) / den if den else 0.0
    return rate / (k + dd)


def _spectrum(x: np.ndarray, rate: int) -> tuple[np.ndarray, np.ndarray]:
    n = 1 << int(np.ceil(np.log2(max(len(x), 256) * 4)))
    return np.fft.rfftfreq(n, 1 / rate), np.abs(np.fft.rfft(x * np.hanning(len(x)), n))


def spectral(x: np.ndarray, rate: int) -> dict:
    """Centroid, 85 % rolloff and flatness (0 tonal, 1 noise) of one stretch."""
    f, s = _spectrum(x, rate)
    p = s ** 2
    band = (f >= 40) & (f <= min(16000, rate / 2 * 0.95))
    tot = float(p.sum()) or 1e-12
    roll = float(f[min(len(f) - 1, int(np.searchsorted(np.cumsum(p), 0.85 * tot)))])
    pb = p[band] + 1e-18
    return {"centroid_hz": round(float((f * p).sum() / tot), 1), "rolloff_hz": round(roll, 1),
            "flatness": round(float(np.exp(np.mean(np.log(pb))) / np.mean(pb)), 4)}


def harmonics(x: np.ndarray, rate: int, f0: float, count: int = 24) -> dict:
    """Levels of the first harmonics in dB below the strongest, odd against even, the fall per octave and how much of the sound is
    harmonic at all (the rest is noise, grit or bell-like inharmonic partials)."""
    f, s = _spectrum(x, rate)
    lobe = 2.0 * rate / max(len(x), 1)                         # the Hann window's main lobe, half width in Hz: a short note smears wider than 2.5 %
    lv, mask = [], np.zeros(len(f), bool)
    for k in range(1, count + 1):
        hz = k * f0
        if hz > rate / 2 * 0.95:
            break
        half = min(max(0.025 * hz, lobe), 0.45 * f0)
        m = (f > hz - half) & (f < hz + half)
        mask |= m
        lv.append(float(s[m].max()) if m.any() else 0.0)
    lv_db = _db(np.array(lv)) - _db(np.array([max(lv) or 1e-9]))[0]
    band = (f >= f0 * 0.8) & (f <= f0 * (len(lv) + 0.5))
    share = float((s[mask & band] ** 2).sum() / ((s[band] ** 2).sum() + 1e-18))
    ks = np.arange(1, len(lv_db) + 1)
    use = (ks <= 16) & (lv_db > -60)
    slope = float(np.polyfit(np.log2(ks[use]), lv_db[use], 1)[0]) if use.sum() >= 3 else -40.0
    odd = [lv_db[k - 1] for k in (3, 5, 7, 9, 11) if k <= len(lv_db)]
    even = [lv_db[k - 1] for k in (2, 4, 6, 8, 10) if k <= len(lv_db)]
    return {"levels_db": [round(float(v), 1) for v in lv_db], "odd_minus_even_db": round(float(np.mean(odd) - np.mean(even)), 1) if odd and even else 0.0,
            "slope_db_per_octave": round(slope, 1), "harmonic_share": round(share, 3)}


def shape_words(h: dict | None, spec: dict) -> str:
    """The nearest basic wave: sine, triangle, square, saw (or noisy, when little of it is harmonic)."""
    if h is None:
        return "noisy" if spec["flatness"] > 0.3 else "complex (no single pitch: chords or a dense part)"
    if h["harmonic_share"] < 0.6:
        return "noisy or inharmonic (bell, metal, grit)"
    upper = h["levels_db"][1:8]
    if not upper or max(upper) < -35:
        return "sine"
    power = np.array([10 ** (v / 10) for v in h["levels_db"]])
    first = float(power[0] / power.sum())                    # a saw keeps 61 % in its fundamental, a square 81 %, a triangle 98 %
    if h["odd_minus_even_db"] > 12:
        return "triangle" if first > 0.95 else "square"
    if first > 0.95:
        return "near sine with a little %s colour" % ("even-harmonic" if h["odd_minus_even_db"] < -6 else "harmonic")
    if h["slope_db_per_octave"] > -3:
        return "bright saw (driven or unfiltered)"
    return "saw" if h["slope_db_per_octave"] > -9 else "filtered saw"


def _note_name(midi: float) -> str:
    n = int(round(midi))
    return "%s%d" % (NOTE_NAMES[n % 12], n // 12 - 1)


def _pitch(m: np.ndarray, rate: int, t0: float, t1: float, fmin: float = 30.0) -> tuple[float | None, float]:
    """Median f0 of a note body (YIN every 20 ms) and its vibrato (cents, standard deviation after the drift is taken out), or None when
    it has no single clear pitch. Only the longest run of frames within 50 cents of each other counts: a legato line can change note
    inside one level envelope, and a note change is not vibrato."""
    n = int(2.2 * rate / fmin)
    f0 = []
    for a in np.arange(t0, max(t0, t1 - n / rate) + 1e-9, 0.02):
        fr = m[int(a * rate): int(a * rate) + n]
        if len(fr) == n and np.sqrt(np.mean(fr ** 2)) > 1e-4:
            f0.append(yin_f0(fr, rate, fmin))
    runs, cur = [], []
    for f in f0:
        if f and cur and abs(1200 * math.log2(f / cur[-1])) <= 50:
            cur.append(f)
        else:
            if cur:
                runs.append(cur)
            cur = [f] if f else []
    if cur:
        runs.append(cur)
    best = max(runs, key=len) if runs else []
    if len(best) < max(2, 0.4 * len(f0)):
        return None, 0.0
    v = np.array(best)
    med = float(np.median(v))
    if len(v) <= 4:
        return med, 0.0
    cents = 1200 * np.log2(v / med)
    i = np.arange(len(cents))
    return med, float(np.std(cents - np.polyval(np.polyfit(i, cents, 1), i)))


def _width(x: np.ndarray) -> dict | None:
    if x.ndim < 2 or x.shape[1] < 2:
        return {"side_minus_mid_db": -120.0, "correlation": 1.0, "word": "mono", "channels": 1}
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    ratio = float(_db(np.array([np.sqrt(np.mean(side ** 2)) / (np.sqrt(np.mean(mid ** 2)) + 1e-12)]))[0])
    c = np.corrcoef(x[:, 0], x[:, 1])[0, 1] if np.std(x[:, 0]) > 0 and np.std(x[:, 1]) > 0 else 1.0
    word = "mono" if ratio < -20 else "narrow" if ratio < -12 else "medium" if ratio < -6 else "wide"
    return {"side_minus_mid_db": round(ratio, 1), "correlation": round(float(c), 3), "word": word}


def _median(rows: list[dict], key: str):
    v = [r[key] for r in rows if r.get(key) is not None]
    return round(float(np.median(v)), 4) if v else None


def _pick(segs: list[tuple], env: np.ndarray, max_notes: int) -> list[int]:
    """The clearest notes: loud, long, and starting from a quiet floor (not smeared into the note before)."""
    e = _db(env)
    score = []
    for i, (s0, s1) in enumerate(segs):
        pk = s0 + int(np.argmax(env[s0:s1]))
        long_enough = (s1 - s0) * HOP_S >= 0.1
        score.append((e[pk] - e[s0]) + 10 * math.log10(max(s1 - s0, 1)) + e[pk] * 0.2 - (0 if long_enough else 1000))
    return sorted(sorted(range(len(segs)), key=lambda i: -score[i])[:max_notes])


def _note_body(m: np.ndarray, rate: int, s0: int, s1: int, env: np.ndarray, hop_s: float) -> tuple[np.ndarray, np.ndarray, float, float]:
    """(onset stretch, body stretch, body start s, body end s) of one note."""
    pk = s0 + int(np.argmax(env[s0:s1]))
    a, b = s0 * hop_s, s1 * hop_s
    onset = m[int(a * rate): int(min(b, a + 0.05) * rate)]
    t0 = pk * hop_s + 0.02
    t1 = min(b, t0 + 0.45)
    return onset, m[int(t0 * rate): int(t1 * rate)], t0, t1


def _note_sound(m: np.ndarray, rate: int, seg: tuple, env: np.ndarray, hop_s: float, nxt) -> dict:
    """Envelope, brightness, pitch and harmonics of one note."""
    s0, s1 = seg
    row = note_envelope(env, s0, s1, hop_s, nxt)
    onset, body, t0, t1 = _note_body(m, rate, s0, s1, env, hop_s)
    if len(body) < int(0.04 * rate):
        return row
    sp, so = spectral(body, rate), spectral(onset, rate) if len(onset) > int(0.01 * rate) else None
    row.update(sp, start_s=round(s0 * hop_s, 3), end_s=round(s1 * hop_s, 3))
    row["onset_brightness_ratio"] = round(so["centroid_hz"] / max(sp["centroid_hz"], 1.0), 2) if so else None
    f0, vib = _pitch(m, rate, t0, t1)
    seg = env[s0:s1]
    rise_end = s0 + int(np.argmax(seg >= 10 ** (-2 / 20) * seg.max()))
    fa = fine_attack(m, rate, s0 * hop_s, rise_end * hop_s + 0.03, f0)
    if fa is not None:
        row["attack_s"] = fa
    if f0:
        h = harmonics(body, rate, f0)
        lv = h["levels_db"]
        if len(lv) > 2 and lv[0] < -12 and int(np.argmax(lv)) == 1:   # the period found may be two notes long: try the octave up
            up = harmonics(body, rate, 2 * f0)
            if up["harmonic_share"] >= 0.9 * h["harmonic_share"]:
                f0, h = 2 * f0, up
        row.update(f0_hz=round(f0, 2), vibrato_cents=round(vib, 1), harmonics=h)
        if len(onset) > int(0.02 * rate):
            row["onset_harmonics"] = harmonics(onset, rate, f0)["levels_db"]
    return row


def describe(x: np.ndarray, rate: int, max_notes: int = 12, hop_s: float = HOP_S) -> dict:
    """Read one stem (or a slice of it). x is (samples,) or (samples, channels)."""
    x = np.asarray(x, dtype=np.float64)
    m = x.mean(axis=1) if x.ndim > 1 else x
    env = envelope(m, rate, hop_s)
    segs = note_segments(env, hop_s) or held_segments(env, hop_s)
    if not segs:
        return {"notes": 0, "reason": "no notes found above the floor"}
    picked = _pick(segs, env, max_notes)
    rows = [_note_sound(m, rate, segs[i], env, hop_s, segs[i + 1][0] if i + 1 < len(segs) else None) for i in picked]
    tonal = [r for r in rows if r.get("harmonics")]
    keys = ("attack_s", "hold_s", "decay_s", "sustain", "release_s", "centroid_hz", "rolloff_hz", "flatness", "onset_brightness_ratio", "length_s")
    out = {"notes": len(segs), "measured": len(rows), **{k: _median(rows, k) for k in keys}}
    gated = [r for r in rows if r.get("gated")]
    out["gated_share"] = round(len(gated) / len(rows), 2)
    if len(gated) > len(rows) / 2:                             # the envelope of the held part, not of the cut: the cut is the note length
        out.update({k: _median(gated, k) for k in ("decay_s", "sustain", "release_s")})
    out["polyphonic"] = len(tonal) < 0.5 * len(rows)
    h = None
    if tonal:
        best = max(tonal, key=lambda r: (r["harmonics"]["harmonic_share"], r["length_s"]))
        h = {k: best["harmonics"][k] for k in ("levels_db", "odd_minus_even_db", "slope_db_per_octave", "harmonic_share")}
        h["onset_levels_db"] = best.get("onset_harmonics")
        midis = [69 + 12 * math.log2(r["f0_hz"] / 440.0) for r in tonal]
        out["register"] = {"median": _note_name(float(np.median(midis))), "low": _note_name(min(midis)), "high": _note_name(max(midis)),
                           "median_midi": round(float(np.median(midis)), 1), "pitched_share": round(len(tonal) / len(rows), 2)}
        out["vibrato_cents"] = _median(tonal, "vibrato_cents")
        out["clearest_note"] = {k: best.get(k) for k in ("start_s", "end_s", "f0_hz")}
    out["audition_notes"] = audition_notes(tonal)
    if out["polyphonic"] and h:
        out["clearest_note_harmonics"], h = h, None           # one pitched note out of a chord part is not the part's tone
    out["harmonics"] = h
    out["width"] = _width(x)
    out["shape"] = shape_words(h, {"flatness": out["flatness"] or 0.0})
    out["words"] = character(out)
    return out


BLEND_TAKE = ("attack_s", "hold_s", "decay_s", "sustain", "release_s", "gated_share", "onset_brightness_ratio", "width")


def blend(original: dict, direction: dict, take: tuple = BLEND_TAKE) -> dict:
    """A target sound for a remix part: the original part's tone (its harmonics, brightness, register, notes) with the envelope, gating,
    filter movement and width of a direction sound (a demo instrument from the variety bank, measured by describe on its solo render).
    The person's rule, 2026-10-26: match what exists, then do something interesting; the original's tone is the match, the direction is
    the twist. Keys the direction lacks stay the original's; the words are written again for the blend."""
    out = dict(original)
    for k in take:
        if direction.get(k) is not None:
            out[k] = direction[k]
    out["words"] = character(out)
    out["blended_from"] = {k: direction.get(k) for k in take if direction.get(k) is not None}
    return out


def audition_notes(rows: list[dict], bpm: float = 120.0, gap_s: float = 0.3) -> list[dict]:
    """The measured notes again, one after another with a gap, as render_serum_sound notes (beats at bpm): a remake played on these is
    compared with the original note for note (compare_part_sound)."""
    out, t = [], 0.0
    for r in sorted(rows, key=lambda r: r.get("start_s") or 0.0)[:8]:
        midi = int(round(69 + 12 * math.log2(r["f0_hz"] / 440.0)))
        length = max(0.05, r["length_s"]) + (0.0 if r.get("gated") else 0.25)   # a ringing note is held past its measured tail
        out.append({"pitch": midi, "start": round(t * bpm / 60, 4), "duration": round(length * bpm / 60, 4), "velocity": 100})
        t += length + gap_s
    return out


def character(d: dict) -> list[str]:
    """Plain words for the brief: how the notes start and end, brightness, width, grit."""
    w = []
    att, sus, dec = d.get("attack_s") or 0.0, d.get("sustain") or 0.0, d.get("decay_s") or 0.0
    w.append("soft, slow attack" if att > 0.06 else "quick attack" if att > 0.015 else "sharp, percussive attack")
    if (d.get("gated_share") or 0.0) > 0.5:
        w.append("notes cut off by their length (staccato or gated), held at %.0f %% before the cut" % (100 * sus))
    else:
        w.append("sustained" if sus >= 0.5 else "plucked (short decay)" if dec < 0.5 else "decaying (long tail)")
    if d.get("polyphonic"):
        w.append("chords or several notes at once")
    if (d.get("onset_brightness_ratio") or 1.0) > 1.3:
        w.append("brightness falls after the attack (filter envelope)")
    h = d.get("harmonics")
    if h and h["slope_db_per_octave"] > -4:
        w.append("lots of upper harmonics (bright or driven)")
    elif h and h["slope_db_per_octave"] < -12:
        w.append("dark, few upper harmonics")
    if (d.get("flatness") or 0.0) > 0.2:
        w.append("noisy or breathy")
    if d.get("width"):
        w.append("mono" if d["width"]["word"] == "mono" else d["width"]["word"] + " stereo image")
    if (d.get("vibrato_cents") or 0.0) > 15:
        w.append("vibrato or pitch movement")
    return w


def cutoff_for(rolloff_hz: float) -> float:
    """serum-mcp cutoff value whose calibrated rolloff is nearest the measured one (log-frequency interpolation)."""
    pts = SERUM_CUTOFF_ROLLOFF
    if rolloff_hz <= pts[0][1]:
        return pts[0][0]
    for (c0, h0), (c1, h1) in zip(pts, pts[1:]):
        if rolloff_hz <= h1:
            return round(c0 + (c1 - c0) * (math.log(rolloff_hz) - math.log(h0)) / (math.log(h1) - math.log(h0)), 3)
    return 1.0


def _frame(levels_db: list[float]) -> list[float]:
    return [round(10 ** (v / 20), 4) if v > -60 else 0.0 for v in levels_db]


# Role defaults for the parts a remix plays. Effects stay light: the production recipe adds the bus chains and the pump.
ROLE_FX = {"sub": [], "bass": [], "stab": [{"type": "FXReverb", "wet": 15.0}], "chords": [{"type": "FXReverb", "wet": 15.0}],
           "pad": [{"type": "FXChorus", "wet": 25.0}, {"type": "FXReverb", "wet": 30.0}], "arp": [{"type": "FXDelay", "wet": 15.0}, {"type": "FXReverb", "wet": 15.0}],
           "pluck": [{"type": "FXReverb", "wet": 15.0}], "lead": [{"type": "FXReverb", "wet": 15.0}], "keys": [{"type": "FXReverb", "wet": 15.0}]}
# A sub is designed to be a sub: it is not asked to copy the bass stem's brightness, harmonics or width (the low end stays mono).
IGNORE = {"sub": ("centroid_ratio", "slope_db", "odd_even_db", "width_db"), "bass": ("width_db",)}
POLY_TABLE = "analog_warm"   # serum-mcp's curated warm analog table, for a chord part that has no single harmonic series to copy
SUB_HARMONICS = 3            # a sub keeps the fundamental and two partials of the measured table; the rest belongs to the parts above it


def starting_point(d: dict, role: str = "", name: str = "") -> dict:
    """A serum-mcp PresetSpec from describe(), complete enough to generate and hear: the measured harmonics as a custom wavetable (body
    frame, then the attack frame when the attack is brighter, with a second envelope moving the table from the attack to the body), the
    measured amp envelope, unison only for a part measured medium or wide (two detuned voices on a near-sine beat), mono for a bass or
    lead, a low-pass on the measured roll-off, light effects by role, and two macros (TONE darkens, BITE adds the attack). Plus notes in
    words for what it leaves to the designer. Field names follow serum-mcp's PresetSpec (its list_parameters)."""
    osc: dict = {"volume": 0.75}
    notes = []
    h = d.get("harmonics")
    moves = bool(h and h.get("onset_levels_db") and (d.get("onset_brightness_ratio") or 1.0) > 1.15)
    if h:
        body = _frame(h["levels_db"])
        if role in ("sub", "bass"):
            body = body[:SUB_HARMONICS] + [0.0] * (len(body) - SUB_HARMONICS)
            moves = False
        osc["custom_harmonics"] = [body] + ([_frame(h["onset_levels_db"])] if moves else [])
        osc["table_position"] = 0.0
        if h["levels_db"] and h["levels_db"][0] < -12:
            notes.append("the fundamental is %.0f dB under the strongest harmonic: check the octave against the part's MIDI before using the table "
                         "(it can sound an octave up), or drop the first entry" % -h["levels_db"][0])
    else:
        osc["wavetable"] = "warm_sub" if role in ("sub", "bass") else POLY_TABLE
        notes.append("no single clear pitch (chords or a dense part): %s chosen from the role; pick the table by ear from the shape and "
                     "brightness, or cut a clear note from the stem as a sample_source" % osc["wavetable"])
    width = (d.get("width") or {}).get("word")
    if width in ("medium", "wide") and role not in ("sub", "bass"):
        osc.update(unison=4.0 if width == "wide" else 2.0, detune=0.25 if width == "wide" else 0.12)
    env = {"attack": max(0.0005, d.get("attack_s") or 0.0005), "hold": d.get("hold_s") or 0.0, "decay": max(0.01, d.get("decay_s") or 0.3),
           "sustain": d.get("sustain") or 0.0, "release": max(0.015, d.get("release_s") or min(0.3, (d.get("decay_s") or 0.3) / 3))}
    if not env["sustain"] and (d.get("gated_share") or 0.0) <= 0.5:
        env["release"] = max(env["release"], env["decay"])     # a sound that dies away by itself keeps dying away after the note-off
    envs = [{k: round(float(v), 4) for k, v in env.items()}]
    routes = []
    if moves:
        envs.append({"attack": 0.0, "hold": 0.0, "decay": round(max(0.03, min(0.2, env["decay"] / 3)), 4), "sustain": 0.0, "release": 0.05})
        routes.append({"source": "env1", "destination": "oscillator0.table_position", "amount": 100.0})
    spec = {"name": name or "CP - Matched %s" % (role or "Part").title(), "description": "Matched to the original's %s: %s" % (role or "part", ", ".join(d.get("words", []))),
            "oscillators": [osc], "envelopes": envs}
    if d.get("rolloff_hz"):
        spec["filters"] = [{"type": "lowpass_24", "cutoff": _cutoff(d, h, role), "resonance": 5.0}]
        spec["macros"] = [{"name": "TONE", "value": 0.0}, {"name": "BITE", "value": 0.0}]
        routes.append({"source": "macro0", "destination": "filter0.cutoff", "amount": -50.0})
        routes.append({"source": "macro1", "destination": "oscillator0.table_position" if moves else "filter0.resonance", "amount": 50.0 if moves else 30.0})
        notes.append("filter: cutoff %.2f from the measured roll-off %.0f Hz (serum-mcp's calibration); the harmonics carry the tone, the filter the "
                     "movement" % (spec["filters"][0]["cutoff"], d["rolloff_hz"]))
    if routes:
        spec["mod_routes"] = routes
    fx = [dict(x) for x in ROLE_FX.get(role, [{"type": "FXReverb", "wet": 15.0}])]
    if width == "narrow" and role not in ("sub", "bass") and not any(x["type"] == "FXChorus" for x in fx):
        fx.insert(0, {"type": "FXChorus", "wet": 15.0})
    if fx:
        spec["fx_chain"] = fx
    if role in ("bass", "sub", "lead"):
        spec["global"] = {"mono": True}
    if (d.get("vibrato_cents") or 0.0) > 15:
        notes.append("about %.0f cents of pitch movement: a slow LFO on pitch, small amount" % d["vibrato_cents"])
    notes.append("Serum's decay curve is not a straight measurement match: render the part, compare_part_sound, then revise")
    return {"spec": spec, "notes": notes}


def _cutoff(d: dict, h: dict | None, role: str) -> float:
    """A low-pass that keeps what the part has: above the last harmonic within 40 dB of the strongest when the table carries the tone
    (a cutoff at the note's own roll-off would remove the harmonics the table was built from), three times the roll-off for a chord
    part, twice it for a sub."""
    f0 = (d.get("clearest_note") or {}).get("f0_hz")
    if h and f0:
        last = max([k + 1 for k, v in enumerate(h["levels_db"]) if v > -40] or [1])
        return round(min(1.0, max(0.7, cutoff_for(f0 * (last + 1) * 1.5))), 3)
    scale = 2.0 if role in ("sub", "bass") else 3.0
    return round(min(1.0, max(0.45 if role in ("sub", "bass") else 0.6, cutoff_for(d["rolloff_hz"] * scale))), 3)


def rolloff_for(cutoff: float) -> float:
    """The inverse of cutoff_for, on the same calibration table."""
    pts = SERUM_CUTOFF_ROLLOFF
    if cutoff <= pts[0][0]:
        return pts[0][1]
    for (c0, h0), (c1, h1) in zip(pts, pts[1:]):
        if cutoff <= c1:
            return math.exp(math.log(h0) + (math.log(h1) - math.log(h0)) * (cutoff - c0) / (c1 - c0))
    return pts[-1][1]


def distance(diff: dict) -> float:
    """How far a remake sits from the original, one number to choose the best round: log ratios of the times and the brightness, the
    sustain step, and the harmonic, width and register differences scaled to about one unit for a clear miss. No differences (a side
    without notes) is the furthest."""
    if not diff:
        return 99.0
    def lr(k):
        v = diff.get(k)
        return abs(math.log2(v)) if v and v > 0 else 0.0
    return round(lr("attack_ratio") + lr("decay_ratio") + lr("release_ratio") + 2 * lr("centroid_ratio") + 2 * abs(diff.get("sustain") or 0.0)
                 + abs(diff.get("slope_db") or 0.0) / 6 + abs(diff.get("odd_even_db") or 0.0) / 12 + abs(diff.get("width_db") or 0.0) / 12
                 + abs(diff.get("register_semitones") or 0.0) / 12, 3)


OPEN_CUTOFF = 0.99   # a filter this open cannot brighten the sound any further


def _add_upper_harmonics(s: dict, ratio: float) -> list[str]:
    """Brighten a remake whose filter is already open: a saw-like partner oscillator (Basic Shapes, the saw frame) mixed in by how dark it
    is, then soft saturation, a little more each round. Found 2026-10-29: Open Your Heart's stab sat at 0.24x the original's brightness
    for two rounds because the only move was the cutoff, already at 1.0."""
    done = []
    oscs = s.setdefault("oscillators", [{}])
    if len(oscs) < 2:
        o0 = oscs[0]
        oscs.append({"volume": round(min(0.6, 0.25 + 0.5 * (1.0 - ratio)), 2), "wavetable": "analog_basic", "table_position": SAW_FRAME,
                     "unison": o0.get("unison", 1.0), "detune": o0.get("detune", 0.0), "octave": o0.get("octave", 0.0)})
        done.append("osc B: a saw at %.2f for upper harmonics" % oscs[1]["volume"])
    fx = s.setdefault("fx_chain", [])
    dist = next((x for x in fx if x.get("type") == "FXDistortion"), None)
    if dist is None:
        dist = {"type": "FXDistortion", "wet": 0.0, "params": {"kParamMode": "kSoftSat", "kParamDrive": 25.0}}
        fx.insert(0, dist)
    else:
        prm = dist.setdefault("params", {})
        prm["kParamDrive"] = min(70.0, float(prm.get("kParamDrive", 25.0)) + 15.0)
    dist["wet"] = min(60.0, float(dist.get("wet", 0.0)) + 25.0)
    done.append("soft saturation %d %% wet, drive %d" % (dist["wet"], dist["params"].get("kParamDrive", 25.0)))
    return done


SAW_FRAME = 170.0    # Basic Shapes runs sine, triangle, saw, square across 0..256


def revise(spec: dict, cmp: dict, orig: dict, role: str = "") -> tuple[dict, list[str]]:
    """The next round's spec from compare(): envelope times scaled by the measured ratios, the sustain set to the original's, the cutoff
    moved along the calibration by the brightness ratio, chorus up or down for width, the octave for register. Harmonic shape is left
    alone (that is a table redesign, said in the list). Returns (new spec, what changed)."""
    import copy
    s, d, done = copy.deepcopy(spec), cmp["differences"], []
    env = s["envelopes"][0]

    def off(k, ratio=True):
        v = d.get(k)
        return v is not None and (abs(v - 1) > TOL[k] if ratio else abs(v) > TOL[k])
    if off("gated_share", False):                              # the render's note-offs cut what rings out in the original, or the reverse
        env["release"] = round(max(env["release"], env["decay"]) if d["gated_share"] > 0 else max(0.015, env["release"] / 3), 4)
        done.append("env0 release %.3f s" % env["release"])
    for key, field in (("attack_ratio", "attack"), ("decay_ratio", "decay"), ("release_ratio", "release")):
        if key == "decay_ratio" and off("gated_share", False):
            continue                                            # a decay read through a cut is the note length, not the patch
        if key == "attack_ratio" and off(key) and abs(d[key] - 1) * (orig.get("attack_s") or 0.0) <= ATTACK_ABS_S:
            continue                                            # a few milliseconds is below what the 1 ms reading can tell apart
        if off(key) and d[key] > 0:
            env[field] = round(min(10.0 if field == "attack" else 32.0, max(0.0005 if field == "attack" else 0.01, env[field] / d[key])), 4)
            done.append("env0 %s %.3f s" % (field, env[field]))
    if off("sustain", False) and orig.get("sustain") is not None:
        env["sustain"] = round(min(1.0, max(0.0, orig["sustain"])), 3)
        done.append("env0 sustain %.2f" % env["sustain"])
    if off("centroid_ratio"):
        f = s.setdefault("filters", [{"type": "lowpass_24", "cutoff": 1.0, "resonance": 5.0}])[0]
        if d["centroid_ratio"] < 1 and f.get("cutoff", 1.0) >= OPEN_CUTOFF:
            done += _add_upper_harmonics(s, d["centroid_ratio"])
        else:
            f["cutoff"] = round(min(1.0, max(0.2, cutoff_for(rolloff_for(f["cutoff"]) / d["centroid_ratio"]))), 3)
            done.append("cutoff %.2f" % f["cutoff"])
    if off("width_db", False):
        fx = s.setdefault("fx_chain", [])
        ch = next((x for x in fx if x["type"] == "FXChorus"), None)
        if d["width_db"] < 0:
            if ch is None:
                ch = {"type": "FXChorus", "wet": 0.0}
                fx.insert(0, ch)
            ch["wet"] = min(60.0, ch["wet"] + 15.0)
        elif ch is not None:
            ch["wet"] = max(0.0, ch["wet"] - 15.0)
        elif s["oscillators"][0].get("unison", 1.0) > 1.0:
            s["oscillators"][0]["unison"] = max(1.0, s["oscillators"][0]["unison"] / 2)
        done.append("width: chorus %s" % (ch["wet"] if ch else "unchanged, unison %s" % s["oscillators"][0].get("unison")))
    if off("register_semitones", False):
        o = s["oscillators"][0]
        o["octave"] = max(-4.0, min(4.0, o.get("octave", 0.0) - round(d["register_semitones"] / 12)))
        done.append("octave %+d" % o["octave"])
    if off("slope_db", False) or off("odd_even_db", False):
        done.append("left for the designer: the harmonic shape differs (slope %+.1f dB per octave, odd against even %+.1f dB)" % (
            d.get("slope_db") or 0.0, d.get("odd_even_db") or 0.0))
    return s, done


def _ratio(a, b):
    return None if not a or not b else round(b / a, 2)


def compare(orig: dict, remake: dict, role: str = "") -> dict:
    """Differences of a remake from the original, and what to change on the patch. Taste stays with the person. A side with no notes
    found is never a match (a silent or broken render compares as nothing, not as equal)."""
    empty = [n for n, x in (("original", orig), ("remake", remake)) if not x.get("measured")]
    if empty:
        return {"differences": {}, "adjust": ["no notes found in the %s: check that it plays" % " and the ".join(empty)], "match": False}
    d = {"attack_ratio": _ratio(orig.get("attack_s"), remake.get("attack_s")), "decay_ratio": _ratio(orig.get("decay_s"), remake.get("decay_s")),
         "sustain": None if orig.get("sustain") is None or remake.get("sustain") is None else round(remake["sustain"] - orig["sustain"], 3),
         "release_ratio": _ratio(orig.get("release_s"), remake.get("release_s")), "centroid_ratio": _ratio(orig.get("centroid_hz"), remake.get("centroid_hz"))}
    ho, hr = orig.get("harmonics"), remake.get("harmonics")
    if ho and hr:
        d["slope_db"] = round(hr["slope_db_per_octave"] - ho["slope_db_per_octave"], 1)
        d["odd_even_db"] = round(hr["odd_minus_even_db"] - ho["odd_minus_even_db"], 1)
    wo, wr = orig.get("width"), remake.get("width")
    if wo and wr:
        d["width_db"] = round(wr["side_minus_mid_db"] - wo["side_minus_mid_db"], 1)
    ro, rr = orig.get("register"), remake.get("register")
    if ro and rr:
        d["register_semitones"] = round(rr["median_midi"] - ro["median_midi"], 1)
    d["gated_share"] = round((remake.get("gated_share") or 0.0) - (orig.get("gated_share") or 0.0), 2)
    for k in IGNORE.get(role, ()):
        d.pop(k, None)
    todo = _adjust(d, orig, remake)
    return {"differences": d, "adjust": todo, "match": not todo}


def _adjust(d: dict, orig: dict, remake: dict) -> list[str]:
    todo = []

    def off(key, ratio=True):
        v = d.get(key)
        return v is not None and (abs(v - 1) > TOL[key] if ratio else abs(v) > TOL[key])
    if off("attack_ratio") and abs(d["attack_ratio"] - 1) * orig["attack_s"] > ATTACK_ABS_S:
        todo.append("attack is %.1fx the original: set env0 attack near %.0f ms" % (d["attack_ratio"], 1000 * orig["attack_s"]))
    if off("decay_ratio"):
        todo.append("decay is %.1fx the original: %s env0 decay" % (d["decay_ratio"], "shorten" if d["decay_ratio"] > 1 else "lengthen"))
    if off("sustain", False):
        todo.append("sustain is %+.2f from the original (%.2f): set env0 sustain near it" % (d["sustain"], orig["sustain"]))
    if off("release_ratio"):
        todo.append("release is %.1fx the original: %s env0 release" % (d["release_ratio"], "shorten" if d["release_ratio"] > 1 else "lengthen"))
    if off("centroid_ratio"):
        todo.append("%s than the original (%.1fx): %s" % ("brighter" if d["centroid_ratio"] > 1 else "darker", d["centroid_ratio"],
                    "lower the cutoff or the upper harmonics" if d["centroid_ratio"] > 1 else "open the cutoff or add upper harmonics"))
    if off("slope_db", False):
        todo.append("upper harmonics fall %+.1f dB per octave against the original: %s" % (d["slope_db"], "less drive or a darker table" if d["slope_db"] > 0 else "more drive or a brighter table"))
    if off("odd_even_db", False):
        todo.append("odd against even harmonics differ by %+.1f dB: %s" % (d["odd_even_db"], "move toward a saw (even harmonics)" if d["odd_even_db"] > 0 else "move toward a square (odd harmonics)"))
    if off("width_db", False):
        todo.append("%s than the original: %s unison detune or chorus" % ("wider" if d["width_db"] > 0 else "narrower", "less" if d["width_db"] > 0 else "more"))
    if off("register_semitones", False):
        todo.append("sits %+.0f semitones from the original's register: change octave" % d["register_semitones"])
    if off("gated_share", False):
        todo.append("the remake's notes are %s where the original's %s: %s env0 release" % (
            "cut off" if d["gated_share"] > 0 else "ringing on", "ring out" if d["gated_share"] > 0 else "are cut off",
            "lengthen" if d["gated_share"] > 0 else "shorten"))
    return todo
