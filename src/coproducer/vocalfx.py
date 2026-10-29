"""Offline vocal clean-up chain for spoken or sampled voice. Pure numpy/scipy; length-preserving so FL clip offsets stay valid.

The chain is deliberately conservative: it is meant to run on a source file once and then be used by many playlist clips.

    y = clean_vocal(x, sr)                 # mono float array in, same length out

Order: high-pass, optional noise reduction, tone, de-ess, compress, parallel saturation, level and peak ceiling.
Every stage is a plain function so a test or a caller can run one alone.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, lfilter, sosfilt, sosfiltfilt


def db(x: float) -> float:
    return 20.0 * np.log10(max(float(x), 1e-12))


def hpf(x: np.ndarray, sr: int, hz: float = 100.0, order: int = 4) -> np.ndarray:
    """Zero-phase high-pass, so it adds no delay."""
    return sosfiltfilt(butter(order, hz, "highpass", fs=sr, output="sos"), x)


def _biquad(kind: str, sr: int, f0: float, gain_db: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """RBJ audio-EQ-cookbook coefficients for 'peak', 'lowshelf' or 'highshelf'."""
    a_ = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2 * q)
    cw = np.cos(w0)
    if kind == "peak":
        b = [1 + alpha * a_, -2 * cw, 1 - alpha * a_]
        a = [1 + alpha / a_, -2 * cw, 1 - alpha / a_]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(a_) * alpha
        b = [a_ * ((a_ + 1) + (a_ - 1) * cw + sq), -2 * a_ * ((a_ - 1) + (a_ + 1) * cw), a_ * ((a_ + 1) + (a_ - 1) * cw - sq)]
        a = [(a_ + 1) - (a_ - 1) * cw + sq, 2 * ((a_ - 1) - (a_ + 1) * cw), (a_ + 1) - (a_ - 1) * cw - sq]
    elif kind == "lowshelf":
        sq = 2 * np.sqrt(a_) * alpha
        b = [a_ * ((a_ + 1) - (a_ - 1) * cw + sq), 2 * a_ * ((a_ - 1) - (a_ + 1) * cw), a_ * ((a_ + 1) - (a_ - 1) * cw - sq)]
        a = [(a_ + 1) + (a_ - 1) * cw + sq, -2 * ((a_ - 1) + (a_ + 1) * cw), (a_ + 1) + (a_ - 1) * cw - sq]
    else:
        raise ValueError(kind)
    b = np.asarray(b) / a[0]
    a = np.asarray(a) / a[0]
    return b, a


def tone(x: np.ndarray, sr: int, bands: list[tuple[str, float, float, float]]) -> np.ndarray:
    """Apply (kind, hz, gain_db, q) biquads in series. Minimum-phase, so the delay is a fraction of a millisecond in the mids."""
    y = x
    for kind, f0, g, q in bands:
        b, a = _biquad(kind, sr, f0, g, q)
        y = lfilter(b, a, y)
    return y


def _env(x: np.ndarray, sr: int, attack_ms: float, release_ms: float) -> np.ndarray:
    """Peak follower with separate attack and release (one-pole), vectorised in blocks for speed."""
    a_att = np.exp(-1.0 / (sr * attack_ms / 1000.0))
    a_rel = np.exp(-1.0 / (sr * release_ms / 1000.0))
    ax = np.abs(x)
    out = np.empty_like(ax)
    e = 0.0
    for i, v in enumerate(ax):                  # a python loop is fine for a few minutes of mono
        e = a_att * e + (1 - a_att) * v if v > e else a_rel * e + (1 - a_rel) * v
        out[i] = e
    return out


def deess(x: np.ndarray, sr: int, lo: float = 5500.0, hi: float = 9500.0, thresh_db: float = -34.0, ratio: float = 3.0) -> np.ndarray:
    """Split-band de-esser: when the sibilant band is over the threshold, turn only that band down."""
    hi = min(hi, 0.45 * sr)
    sos = butter(4, [lo, hi], "bandpass", fs=sr, output="sos")
    band = sosfilt(sos, x)
    env = _env(band, sr, 1.0, 40.0)
    over = np.maximum(20 * np.log10(env + 1e-9) - thresh_db, 0.0)
    gain = 10 ** (-(over * (1 - 1 / ratio)) / 20.0)
    return x - band * (1 - gain)


def compress(x: np.ndarray, sr: int, thresh_db: float = -24.0, ratio: float = 3.5, attack_ms: float = 5.0, release_ms: float = 90.0,
             knee_db: float = 6.0, makeup_db: float | None = None) -> np.ndarray:
    """Feed-forward compressor with a soft knee. makeup_db None keeps the loud-part RMS where it was."""
    env = _env(x, sr, attack_ms, release_ms)
    lev = 20 * np.log10(env + 1e-9)
    over = lev - thresh_db
    gr = np.where(over <= -knee_db / 2, 0.0,
                  np.where(over >= knee_db / 2, over * (1 - 1 / ratio), (over + knee_db / 2) ** 2 / (2 * knee_db) * (1 - 1 / ratio)))
    n = int(0.002 * sr)                          # offline look-ahead: pull the gain curve 2 ms earlier, so there is no added delay
    if n:
        gr = np.concatenate([gr[n:], np.full(n, gr[-1])])
    y = x * 10 ** (-gr / 20.0)
    if makeup_db is None:
        loud = np.abs(x) > 10 ** (thresh_db / 20.0)
        if loud.sum() > 100:
            makeup_db = db(np.sqrt(np.mean(x[loud] ** 2))) - db(np.sqrt(np.mean(y[loud] ** 2)))
        else:
            makeup_db = 0.0
    return y * 10 ** (makeup_db / 20.0)


def saturate(x: np.ndarray, drive: float = 2.5, mix: float = 0.25) -> np.ndarray:
    """Parallel tanh saturation: adds harmonics for density without changing the peaks much."""
    wet = np.tanh(drive * x) / np.tanh(drive)
    return (1 - mix) * x + mix * wet


def reduce_noise(x: np.ndarray, sr: int, amount: float = 0.6) -> np.ndarray:
    """Stationary spectral subtraction with the noise profile taken from the quietest 8% of 50 ms frames. Needs noisereduce."""
    try:
        import noisereduce as nr
    except ImportError:                          # optional: the rest of the chain still works
        return x
    fr = int(0.05 * sr)
    n = len(x) // fr
    if n < 20:
        return x
    rms = np.sqrt(np.mean(x[: n * fr].reshape(n, fr) ** 2, axis=1))
    quiet = np.argsort(rms)[: max(4, int(n * 0.08))]
    noise = np.concatenate([x[i * fr:(i + 1) * fr] for i in sorted(quiet)])
    return nr.reduce_noise(y=x, sr=sr, y_noise=noise, stationary=True, prop_decrease=amount, n_fft=2048)


def soft_ceiling(x: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
    c = 10 ** (ceiling_db / 20.0)
    return c * np.tanh(x / c) if np.max(np.abs(x)) > c else x


DEFAULT_TONE = [
    ("peak", 250.0, -3.5, 0.8),       # low-mid boxiness
    ("peak", 3200.0, 3.0, 0.9),       # presence
    ("highshelf", 9000.0, 1.5, 0.7),  # air
]


def clean_vocal(x: np.ndarray, sr: int, *, hpf_hz: float = 100.0, nr_amount: float = 0.6, tone_bands=None, target_rms_db: float | None = None,
                comp_thresh_db: float = -26.0, sat_mix: float = 0.22, ceiling_db: float = -1.0) -> np.ndarray:
    """Mono float in, same-length mono float out. target_rms_db is the RMS of the voiced parts; None keeps the level the file had,
    which preserves a balance the producer already set between clips."""
    x = np.asarray(x, dtype=np.float64)
    voiced_in = np.abs(x) > 10 ** (-40 / 20.0)
    keep_db = db(np.sqrt(np.mean(x[voiced_in] ** 2))) if voiced_in.sum() > 100 else None
    if target_rms_db is None:
        target_rms_db = keep_db
    y = hpf(x, sr, hpf_hz)
    y = reduce_noise(y, sr, nr_amount) if nr_amount > 0 else y
    y = tone(y, sr, tone_bands if tone_bands is not None else DEFAULT_TONE)
    y = deess(y, sr)
    y = compress(y, sr, thresh_db=comp_thresh_db)
    y = saturate(y, 2.5, sat_mix)
    voiced = np.abs(y) > 10 ** (-40 / 20.0)
    if voiced.sum() > 100 and target_rms_db is not None:
        y = y * 10 ** ((target_rms_db - db(np.sqrt(np.mean(y[voiced] ** 2)))) / 20.0)
    return soft_ceiling(y, ceiling_db)
