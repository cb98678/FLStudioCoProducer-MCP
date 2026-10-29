"""A club master from a finished mixdown, to a targets file: gain into a soft clipper, then a look-ahead true-peak limiter, iterated until the
integrated loudness lands on target or the crest-factor floor stops it.

Why a DSP stage and not only FL's Maximus: Maximus' settings live in an opaque plugin state the file patcher cannot set, and the loop has to hit a
number. This is the delivery step after the mix (the arrangement and the parts stay editable in FL); the FL master chain keeps headroom
(no limiter, or Maximus with a ceiling) so the stage has room. The clipper takes the fast transients first, which is how club masters reach
-7 to -9 LUFS with a crest near 7.5 dB (iZotope 2025, TrackSensei 2026, see targets/club_release.toml); the limiter then catches the
inter-sample peaks on a 4x oversampled detector. A loudness the crest floor forbids is reported, not forced: it needs mix changes.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, resample_poly, sosfiltfilt

from . import dsp


def prepare(x: np.ndarray, rate: int, hp_hz: float = 5.0, floor_db: float = -80.0, keep_s: float = 0.25, mono_below_hz: float = 0.0) -> tuple[np.ndarray, dict]:
    """Clean a mixdown before mastering: remove DC with a zero-phase high-pass at hp_hz (0.03 dB at 30 Hz, so the sub is untouched); with
    mono_below_hz, high-pass the side signal there so the lows are mono (a techno render had its lows 13 dB under mid, the target is 20);
    then cut a tail that has gone quiet (50 ms RMS under floor_db) after keep_s, with a 20 ms fade. A held DC offset once kept FL's render
    running 33 s past the song's end (2026-10-25). Returns (audio, {"dc_before", "trimmed_s", "mono_below_hz"})."""
    x2 = x if x.ndim == 2 else x[:, None]
    dc = [round(float(v), 5) for v in x2.mean(axis=0)]
    y = sosfiltfilt(butter(2, hp_hz, btype="highpass", fs=rate, output="sos"), x2, axis=0) if len(x2) > 3 * rate // max(int(hp_hz), 1) else x2 - x2.mean(axis=0)
    if mono_below_hz > 0 and y.shape[1] == 2 and len(y) > rate:
        mid, side = (y[:, 0] + y[:, 1]) / 2, (y[:, 0] - y[:, 1]) / 2
        side = sosfiltfilt(butter(4, mono_below_hz, btype="highpass", fs=rate, output="sos"), side)
        y = np.stack([mid + side, mid - side], axis=1)
    hop = max(1, rate // 20)
    n = len(y) // hop
    rms = np.sqrt((y[: n * hop] ** 2).reshape(n, hop, -1).mean(axis=(1, 2))) if n else np.zeros(0)
    loud = np.where(rms > 10 ** (floor_db / 20))[0]
    end = min(len(y), (int(loud[-1]) + 1) * hop + int(keep_s * rate)) if len(loud) else len(y)
    y = y[:end].copy()
    f = min(len(y), int(0.02 * rate))
    if end < len(x2) and f:
        y[-f:] *= np.linspace(1.0, 0.0, f)[:, None]
    return (y if x.ndim == 2 else y[:, 0]), {"dc_before": dc, "trimmed_s": round((len(x2) - end) / rate, 2), "mono_below_hz": mono_below_hz}


def soft_clip(x: np.ndarray, ceiling: float, knee: float = 0.25) -> np.ndarray:
    """Linear below ceiling * (1 - knee), then a tanh curve that never passes ceiling."""
    t = ceiling * (1.0 - knee)
    a = np.abs(x)
    over = a > t
    y = x.copy()
    span = ceiling - t
    y[over] = np.sign(x[over]) * (t + span * np.tanh((a[over] - t) / span))
    return y


def limit(x: np.ndarray, rate: int, ceiling: float, lookahead_ms: float = 5.0, release_ms: float = 80.0, oversample: int = 4) -> tuple[np.ndarray, float]:
    """A look-ahead peak limiter on the oversampled peak of all channels. The gain is computed on a 1 ms grid (the smallest gain in each block,
    so no peak slips through), with instant attack across the look-ahead and an exponential release, then interpolated back.
    Returns (limited signal, most gain reduction in dB)."""
    x2 = x if x.ndim == 2 else x[:, None]
    n = len(x2)
    up = np.abs(resample_poly(x2, oversample, 1, axis=0)).max(axis=1)[: n * oversample]
    peak = np.pad(up, (0, n * oversample - len(up))).reshape(n, oversample).max(axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-12))
    blk = max(1, rate // 1000)
    nb = -(-n // blk)
    gb = np.pad(need, (0, nb * blk - n), constant_values=1.0).reshape(nb, blk).min(axis=1)
    la = max(1, int(round(lookahead_ms / 1000 * rate / blk)))
    ahead = np.lib.stride_tricks.sliding_window_view(np.concatenate([gb, np.ones(la)]), la + 1).min(axis=1)[:nb]
    rel = np.exp(-1.0 / max(release_ms / 1000 * rate / blk, 1.0))
    g = np.empty(nb)
    cur = 1.0
    for i, w in enumerate(ahead.tolist()):
        cur = w if w < cur else rel * cur + (1 - rel) * w
        g[i] = cur
    centers = np.arange(nb) * blk + blk / 2
    gain = np.minimum(np.interp(np.arange(n), centers, g), np.repeat(ahead, blk)[:n])
    y = x2 * gain[:, None]
    return (y if x.ndim == 2 else y[:, 0]), float(20 * np.log10(gain.min() + 1e-12))


def master(x: np.ndarray, rate: int, target_lufs: float, tp_ceiling_db: float, crest_floor_db: float = 6.5, clip_ceiling_db: float = -1.0,
           iterations: int = 8, tolerance_lu: float = 0.2) -> dict:
    """Raise the mix to target_lufs through the clipper and the limiter. Returns {"audio", "lufs", "true_peak_dbtp", "crest_db", "gain_db",
    "limiter_gr_db", "stopped"}; stopped names what kept it from the target (crest_floor) or is empty."""
    lo, hi = -24.0, 30.0
    gain = target_lufs - dsp.integrated_loudness(x, rate)
    best = None
    tp_lin = 10 ** (tp_ceiling_db / 20)
    clip_lin = 10 ** (min(clip_ceiling_db, tp_ceiling_db + 0.5) / 20)
    for _ in range(iterations):
        y = soft_clip(x * 10 ** (gain / 20), clip_lin)
        y = y - y.mean(axis=0)  # clipping one-sided kick peaks makes a little DC (-59 dBFS on a house master, 2026-10-25); take it out before limiting
        y, gr = limit(y, rate, tp_lin * 0.995)
        lufs = float(dsp.integrated_loudness(y, rate))
        rms = float(np.sqrt(np.mean(y ** 2)))
        crest = float(20 * np.log10(np.abs(y).max() / max(rms, 1e-12)))
        row = {"audio": y, "lufs": round(lufs, 2), "true_peak_dbtp": round(float(20 * np.log10(dsp.true_peak(y, rate) + 1e-12)), 2), "crest_db": round(crest, 2),
               "gain_db": round(gain, 2), "limiter_gr_db": round(gr, 2), "stopped": ""}
        if crest < crest_floor_db:
            hi = gain
            row["stopped"] = "crest_floor"
        else:
            best = row
            if abs(lufs - target_lufs) <= tolerance_lu:
                return row
            if lufs < target_lufs:
                lo = gain
            else:
                hi = gain
        gain = (lo + hi) / 2 if (best is None or row["stopped"]) else gain + (target_lufs - lufs)
        gain = min(max(gain, lo), hi)
    if best is None:
        best = row
    if abs(best["lufs"] - target_lufs) > tolerance_lu and not best["stopped"]:
        best["stopped"] = "crest_floor" if hi < 30.0 else "iterations"
    return best
