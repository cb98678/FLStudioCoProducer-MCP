"""Tonal balance: the long-term average spectrum of a track in third-octave bands, a profile built from the person's reference tracks, and a
broad match EQ toward that profile.

The method follows published match-EQ and tonal-balance practice (checked 2026-10-25): compare average spectra at equal level, act only broadly
(heavy smoothing; low smoothing turns a match EQ into a resonator), leave the lowest bass alone because songs in other keys have other
fundamentals (iZotope's walkthrough bounds the match at 35 Hz) and keep the top octave controlled because small changes there are loud, and judge
a master against the spread of several references rather than one track (Tonal Balance Control shows a range per band; more references give a
smoother target). Sources: https://www.izotope.com/en/learn/how-to-use-match-eq-in-ozone-9 and
https://www.izotope.com/en/learn/leveling-up-your-mastering-workflow-with-tonal-balance-control
"""
from __future__ import annotations

import numpy as np
from scipy import signal

CENTERS_HZ = [round(float(c), 1) for c in 1000.0 * 2.0 ** (np.arange(-16, 13) / 3.0)]  # 25 Hz to 16 kHz, 29 third-octave bands
NORM_HZ = (100.0, 10000.0)  # band levels are shifted so their mean over this span is 0 dB: shape is compared, not level


def band_levels(x: np.ndarray, rate: int) -> list[float]:
    """Third-octave band levels (dB) of the mono sum's long-term average spectrum, normalized over NORM_HZ."""
    m = x.mean(axis=1) if x.ndim == 2 else x
    n = min(16384, len(m))
    f, p = signal.welch(m, fs=rate, nperseg=n, noverlap=n // 2)
    out = []
    for c in CENTERS_HZ:
        sel = (f >= c / 2 ** (1 / 6)) & (f < min(c * 2 ** (1 / 6), rate / 2))
        out.append(10.0 * np.log10(float(p[sel].sum()) + 1e-20))
    lv = np.array(out)
    mid = [(NORM_HZ[0] <= c <= NORM_HZ[1]) for c in CENTERS_HZ]
    return [round(float(v), 2) for v in lv - lv[mid].mean()]


def profile(levels: list[list[float]], min_spread_db: float = 1.0) -> dict:
    """Mean and spread per band over several tracks' band_levels; the spread is never under min_spread_db (one reference has no spread)."""
    a = np.array(levels, dtype=float)
    spread = np.maximum(a.std(axis=0), min_spread_db) if len(a) > 1 else np.full(a.shape[1], min_spread_db)
    return {"centers_hz": CENTERS_HZ, "mean_db": [round(float(v), 2) for v in a.mean(axis=0)], "spread_db": [round(float(v), 2) for v in spread],
            "tracks": len(a)}


def deviation(own: list[float], prof: dict) -> dict:
    """How far a track sits outside the profile's range: dB beyond mean +/- spread per band, the worst band and how many bands are outside."""
    d = np.array(own) - np.array(prof["mean_db"])
    s = np.array(prof["spread_db"])
    beyond = np.sign(d) * np.maximum(np.abs(d) - s, 0.0)
    worst = int(np.argmax(np.abs(beyond)))
    return {"beyond_db": [round(float(v), 2) for v in beyond], "outside": int((np.abs(beyond) > 0).sum()),
            "worst_hz": prof["centers_hz"][worst], "worst_db": round(float(beyond[worst]), 2), "rms_db": round(float(np.sqrt((beyond ** 2).mean())), 2)}


def match_gains(own: list[float], prof: dict, amount: float = 0.7, max_db: float = 4.0, lo_hz: float = 35.0, hi_hz: float = 12000.0) -> list[float]:
    """EQ gains (dB per band) that move a track toward the profile: only the part outside the references' range, smoothed over about an octave,
    scaled by amount, capped at max_db, and faded to 0 below lo_hz and above hi_hz."""
    beyond = -np.array(deviation(own, prof)["beyond_db"])
    k = np.array([0.25, 0.5, 0.25])
    g = np.convolve(np.convolve(np.pad(beyond, 2, mode="edge"), k, mode="same"), k, mode="same")[2:-2]
    c = np.array(prof["centers_hz"])
    fade = np.clip(np.minimum(np.log2(c / lo_hz) * 3 + 1, np.log2(hi_hz / c) * 3 + 1), 0.0, 1.0)
    return [round(float(v), 2) for v in np.clip(g * amount * fade, -max_db, max_db)]


def apply_eq(x: np.ndarray, rate: int, gains_db: list[float], centers_hz: list[float] | None = None, numtaps: int = 8191) -> np.ndarray:
    """Apply band gains as one linear-phase FIR (the response is interpolated on a log-frequency axis between band centers; 0 dB at DC and
    Nyquist when the outer bands are 0), with the filter's delay removed so the result lines up with the input."""
    c = list(centers_hz or CENTERS_HZ)
    nyq = rate / 2.0
    pts = [(f, g) for f, g in zip(c, gains_db) if f < nyq * 0.98]
    freqs = np.geomspace(10.0, nyq * 0.999, 512)
    gdb = np.interp(np.log(freqs), np.log([p[0] for p in pts]), [p[1] for p in pts])
    fgrid = np.concatenate([[0.0], freqs, [nyq]]) / nyq
    amp = 10 ** (np.concatenate([[gdb[0]], gdb, [gdb[-1]]]) / 20)
    taps = signal.firwin2(numtaps | 1, fgrid, amp)
    y = signal.fftconvolve(x if x.ndim == 2 else x[:, None], taps[:, None], mode="full", axes=0)
    d = (len(taps) - 1) // 2
    y = y[d : d + len(x)]
    return y if x.ndim == 2 else y[:, 0]
