"""Effects baked into vocal chop one-shots: a tempo-synced ping-pong echo. numpy and scipy only.

A chop that needs an echo becomes its own sample (name_echo.wav on its own sampler channel), so the effect stays visible and the dry chop stays editable.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt


def echo(x: np.ndarray, rate: int, bpm: float, delay_beats: float = 0.75, feedback: float = 0.5, repeats: int = 5, lp_hz: float = 3800.0, hp_hz: float = 250.0,
         wet: float = 0.8, tail_s: float = 0.3) -> np.ndarray:
    """Dry chop plus `repeats` echoes, each delay_beats later and `feedback` times quieter, darker each time, alternating left and right.

    x is (frames, 2) or (frames,); the result is stereo and longer by repeats * delay + tail_s. The dry signal stays at its original level.
    """
    s = np.stack([x, x], 1) if x.ndim == 1 else x
    d = int(round(delay_beats * 60.0 / bpm * rate))
    out = np.zeros((len(s) + repeats * d + int(tail_s * rate), 2))
    out[: len(s)] += s
    lp = butter(1, lp_hz, btype="low", fs=rate, output="sos")
    hp = butter(2, hp_hz, btype="high", fs=rate, output="sos")
    cur = sosfilt(hp, s, axis=0)
    for i in range(1, repeats + 1):
        cur = sosfilt(lp, cur, axis=0) * feedback
        mono = cur.mean(axis=1)
        pan = 1.0 if i % 2 else -1.0  # ping-pong
        left, right = mono * (0.5 - 0.4 * pan), mono * (0.5 + 0.4 * pan)
        a = i * d
        out[a : a + len(s), 0] += wet * 2 * left
        out[a : a + len(s), 1] += wet * 2 * right
    k = int(0.05 * rate)
    out[-k:] *= np.linspace(1, 0, k)[:, None]
    return out
