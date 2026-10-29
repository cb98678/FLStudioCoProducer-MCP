"""Synthetic audio for tests and examples: every generator returns float64 arrays shaped (samples, channels)."""
from __future__ import annotations

import numpy as np

RATE = 48000


def sine(freq: float, seconds: float = 2.0, amp: float = 1.0, rate: int = RATE, phase: float = 0.0, channels: int = 1) -> np.ndarray:
    t = np.arange(int(seconds * rate)) / rate
    return np.tile((amp * np.sin(2 * np.pi * freq * t + phase))[:, None], (1, channels))


def noise(seconds: float = 2.0, amp: float = 0.1, rate: int = RATE, channels: int = 2, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, amp, (int(seconds * rate), channels))


def silence(seconds: float = 1.0, rate: int = RATE, channels: int = 1) -> np.ndarray:
    return np.zeros((int(seconds * rate), channels))


def kick(rate: int = RATE, length_s: float = 0.4, amp: float = 0.9) -> np.ndarray:
    t = np.arange(int(length_s * rate)) / rate
    freq = 45 + 110 * np.exp(-t * 30)
    return (amp * np.sin(2 * np.pi * np.cumsum(freq) / rate) * np.exp(-t * 9))[:, None]


def hat(rate: int = RATE, length_s: float = 0.08, amp: float = 0.3, seed: int = 1) -> np.ndarray:
    n = int(length_s * rate)
    return (amp * np.random.default_rng(seed).normal(0, 1, n) * np.exp(-np.arange(n) / (0.012 * rate)))[:, None]


def drum_loop(bpm: float = 140.0, bars: int = 4, rate: int = RATE, channels: int = 2) -> np.ndarray:
    """Four-on-the-floor kick with offbeat hats, a bar of 4 beats each."""
    beat = 60.0 / bpm
    x = np.zeros((int(bars * 4 * beat * rate) + rate // 2, 1))
    for i in range(bars * 4):
        k, h = int(i * beat * rate), int((i + 0.5) * beat * rate)
        x[k:k + len(kick(rate))] += kick(rate)[: len(x) - k]
        x[h:h + len(hat(rate))] += hat(rate)[: len(x) - h]
    return np.tile(x, (1, channels))


def chord(freqs: list[float], seconds: float = 2.0, rate: int = RATE, amp: float = 0.5) -> np.ndarray:
    return sum(sine(f, seconds, amp / len(freqs), rate) for f in freqs)  # type: ignore[return-value]


def to_wav(path: str, x: np.ndarray, rate: int = RATE, subtype: str = "FLOAT") -> str:
    import soundfile as sf
    sf.write(path, x, rate, subtype=subtype)
    return path
