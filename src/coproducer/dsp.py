"""Shared DSP library for the L4 measure modules.

This is ordinary tested library code, not a module: the module linter allows `coproducer.dsp` as an import for
pure and file-reading modules so that each measure module stays a thin, readable call. Everything here works on
float64 arrays shaped (samples, channels). No function mutates its input.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import signal

FLOOR_DB = -120.0
# BS.1770 K-weighting stage constants (the same ones pyloudnorm derives its filters from)
_SHELF = dict(gain_db=3.999843853973347, q=0.7071752369554196, fc=1681.9744509555319)
_HIPASS = dict(q=0.5003270373238773, fc=38.13547087613982)
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
DEFAULT_BANDS = {"sub": (20, 60), "bass": (60, 250), "low_mid": (250, 500), "mid": (500, 2000),
                 "high_mid": (2000, 4000), "presence": (4000, 8000), "air": (8000, 20000)}


# ----------------------------------------------------------------------------- file and level helpers
def load_audio(path: str, max_seconds: float = 0.0) -> tuple[np.ndarray, int]:
    """Read an audio file as float64 (samples, channels). Raises ValueError when it cannot be read."""
    import soundfile as sf
    try:
        frames = int(max_seconds * sf.info(path).samplerate) if max_seconds > 0 else -1
        x, rate = sf.read(path, frames=frames, dtype="float64", always_2d=True)
    except (RuntimeError, OSError) as e:
        raise ValueError(f"cannot read audio file: {e}") from e
    if x.shape[0] == 0:
        raise ValueError("audio file has no samples")
    return x, int(rate)


def db(x: float, floor: float = FLOOR_DB) -> float:
    """Amplitude ratio to dB, clamped at floor."""
    return max(floor, 20.0 * math.log10(x)) if x > 0 else floor


def power_db(x: float, floor: float = FLOOR_DB) -> float:
    return max(floor, 10.0 * math.log10(x)) if x > 0 else floor


def mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1)


# ----------------------------------------------------------------------------- loudness
def _biquad_shelf(rate: int) -> tuple[np.ndarray, np.ndarray]:
    """BS.1770 pre-filter (head-related high shelf), bilinear design as in Brecht De Man's loudness.py."""
    k = math.tan(math.pi * _SHELF["fc"] / rate)
    vh = 10 ** (_SHELF["gain_db"] / 20)
    vb = vh ** 0.499666774155
    q = _SHELF["q"]
    a0 = 1.0 + k / q + k * k
    b = np.array([(vh + vb * k / q + k * k) / a0, 2.0 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0])
    return b, np.array([1.0, 2.0 * (k * k - 1.0) / a0, (1.0 - k / q + k * k) / a0])


def _biquad_highpass(rate: int) -> tuple[np.ndarray, np.ndarray]:
    """BS.1770 revised low-frequency B-weighting stage (b = 1, -2, 1)."""
    k = math.tan(math.pi * _HIPASS["fc"] / rate)
    q = _HIPASS["q"]
    d = 1.0 + k / q + k * k
    return np.array([1.0, -2.0, 1.0]), np.array([1.0, 2.0 * (k * k - 1.0) / d, (1.0 - k / q + k * k) / d])


def k_weight(x: np.ndarray, rate: int) -> np.ndarray:
    """Apply the BS.1770 K-weighting filter (head-shelf then revised low-frequency high-pass) to every channel."""
    out = x
    for b, a in (_biquad_shelf(rate), _biquad_highpass(rate)):
        out = signal.lfilter(b, a, out, axis=0)
    return out


def _channel_gains(n: int) -> np.ndarray:
    return np.array([1.0, 1.0, 1.0, 1.41, 1.41][:n] + [1.0] * max(0, n - 5))


def window_loudness(x: np.ndarray, rate: int, win_s: float, hop_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (window start seconds, loudness in LUFS) for sliding windows over K-weighted audio, ungated."""
    k = k_weight(x, rate)
    sq = np.vstack([np.zeros((1, k.shape[1])), np.cumsum(k * k, axis=0)])
    n, step = int(round(win_s * rate)), max(1, int(round(hop_s * rate)))
    starts = np.arange(0, k.shape[0] - n + 1, step)
    if len(starts) == 0:
        return np.array([]), np.array([])
    ms = (sq[starts + n] - sq[starts]) / n
    z = (ms * _channel_gains(k.shape[1])).sum(axis=1)
    with np.errstate(divide="ignore"):
        lufs = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    return starts / rate, lufs


def integrated_loudness(x: np.ndarray, rate: int) -> float:
    """BS.1770-4 / EBU R128 integrated loudness in LUFS: 400 ms blocks, 75% overlap, -70 LUFS and -10 LU gates."""
    _, lufs = window_loudness(x, rate, 0.4, 0.1)
    if len(lufs) == 0:
        raise ValueError("audio is shorter than one 400 ms block")
    z = 10 ** ((lufs + 0.691) / 10)
    loud = lufs >= -70.0
    if not loud.any():
        return FLOOR_DB
    rel = -0.691 + 10 * math.log10(float(z[loud].mean())) - 10.0
    keep = loud & (lufs >= rel)
    return -0.691 + 10 * math.log10(float(z[keep].mean()))


def loudness_range(lufs: np.ndarray) -> tuple[float, float, float]:
    """EBU Tech 3342 loudness range from short-term values: returns (LRA in LU, low percentile, high percentile)."""
    v = lufs[lufs > -70.0]
    if v.size == 0:
        return 0.0, FLOOR_DB, FLOOR_DB
    mean_energy = 10 * math.log10(np.mean(10 ** (v / 10)))
    v = v[v > mean_energy - 20.0]
    if v.size == 0:
        return 0.0, FLOOR_DB, FLOOR_DB
    lo, hi = np.percentile(v, 10), np.percentile(v, 95)
    return float(hi - lo), float(lo), float(hi)


# ----------------------------------------------------------------------------- peaks and stereo
def true_peak(x: np.ndarray, rate: int, oversample: int = 4) -> float:
    """Linear true peak: the largest absolute value after band-limited oversampling (BS.1770 Annex 2 style)."""
    up = signal.resample_poly(x, oversample, 1, axis=0)
    return float(np.max(np.abs(up)))


def correlation(left: np.ndarray, right: np.ndarray) -> float:
    d = math.sqrt(float(np.dot(left, left)) * float(np.dot(right, right)))
    return float(np.dot(left, right) / d) if d > 0 else 0.0


# ----------------------------------------------------------------------------- spectrum
def avg_power_spectrum(x: np.ndarray, rate: int, nperseg: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    """Welch power spectrum of the mono mix: (frequencies, power)."""
    m = mono(x) if x.ndim == 2 else x
    f, p = signal.welch(m, fs=rate, nperseg=min(nperseg, len(m)), noverlap=min(nperseg, len(m)) // 2)
    return f, p


def band_energy_db(x: np.ndarray, rate: int, bands: dict) -> dict:
    """Energy of each named (low, high) band in dB relative to the total energy up to Nyquist."""
    f, p = avg_power_spectrum(x, rate)
    total = float(np.sum(p)) or 1e-30
    out = {}
    for name, (lo, hi) in bands.items():
        sel = (f >= lo) & (f < min(hi, rate / 2))
        out[name] = round(power_db(float(np.sum(p[sel])) / total), 2)
    return out


def spectral_centroid(x: np.ndarray, rate: int) -> float:
    f, p = avg_power_spectrum(x, rate)
    s = float(np.sum(p))
    return float(np.sum(f * p) / s) if s > 0 else 0.0


def stft_mag(m: np.ndarray, n_fft: int = 2048, hop: int = 512) -> np.ndarray:
    """Magnitude STFT, shape (frames, bins), Hann window."""
    if len(m) < n_fft:
        m = np.pad(m, (0, n_fft - len(m)))
    _, _, z = signal.stft(m, nperseg=n_fft, noverlap=n_fft - hop, window="hann", boundary=None, padded=False)
    return np.abs(z).T


# ----------------------------------------------------------------------------- tempo, key, sections, alignment
def tempo_ambiguity(cands: list[dict]) -> dict:
    """Is the top tempo candidate trustworthy on its own? No when a close rival exists or a 2:1 or 3:2 relative of the
    top candidate carries real strength: those are the usual wrong answers (128 read as 64 or 85). Returns the flag
    and the relatives found, so a caller can ask for a hint instead of guessing."""
    if len(cands) < 2:
        return {"ambiguous": False, "relatives": []}
    top = cands[0]
    rel = []
    for c in cands[1:]:
        ratio = c["bpm"] / top["bpm"]
        share = c["strength"] / top["strength"] if top["strength"] > 0 else 0.0
        for label, target, need in (("double", 2.0, 0.2), ("half", 0.5, 0.2), ("3:2", 1.5, 0.4), ("2:3", 2 / 3, 0.4), ("4:3", 4 / 3, 0.4), ("3:4", 0.75, 0.4)):
            if abs(ratio / target - 1) <= 0.03 and share >= need:
                rel.append({"bpm": c["bpm"], "relation": label, "strength_vs_top": round(share, 2)})
                break
    close_rival = cands[1]["strength"] >= 0.9 * top["strength"]
    return {"ambiguous": bool(close_rival or rel), "relatives": rel}


def estimate_tempo(x: np.ndarray, rate: int, lo: float = 60.0, hi: float = 200.0) -> list[dict]:
    """Rank tempo candidates from the autocorrelation of the spectral-flux onset envelope. Best first."""
    hop = 512
    mag = np.log1p(10 * stft_mag(mono(x), 2048, hop))
    if mag.shape[0] < 64:  # under about 1.5 seconds there is nothing to correlate
        return []
    flux = np.maximum(np.diff(mag, axis=0), 0).sum(axis=1)
    flux = flux - flux.mean()
    ac = signal.correlate(flux, flux, mode="full")[len(flux) - 1:]
    ac /= ac[0] if ac[0] > 0 else 1.0
    fps = rate / hop
    lags = np.arange(int(fps * 60 / hi), min(int(fps * 60 / lo) + 1, len(ac) - 1))
    if len(lags) < 3:
        return []
    bpms = 60.0 * fps / lags
    weight = np.exp(-0.5 * (np.log2(bpms / 130.0) / 1.4) ** 2)
    score = ac[lags] * weight
    peaks, _ = signal.find_peaks(score)
    order = peaks[np.argsort(score[peaks])[::-1]][:5]
    out = []
    for i in order:
        lag = float(lags[i])
        if 0 < i < len(lags) - 1:  # parabolic refinement of the peak
            a, b, c = score[i - 1], score[i], score[i + 1]
            lag += 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
        out.append({"bpm": round(60.0 * fps / lag, 2), "strength": round(float(score[i]), 4)})
    return out


def chroma_vector(x: np.ndarray, rate: int) -> np.ndarray:
    """Pitch-class energy (12 values summing to 1) from the average spectrum between 55 Hz and 2 kHz."""
    f, p = avg_power_spectrum(x, rate, nperseg=16384)
    sel = (f >= 55) & (f <= 2000)
    pc = np.round(12 * np.log2(f[sel] / 440.0)).astype(int) % 12
    chroma = np.zeros(12)
    np.add.at(chroma, (pc + 9) % 12, p[sel])
    s = chroma.sum()
    return chroma / s if s > 0 else chroma


def estimate_key(x: np.ndarray, rate: int) -> dict:
    """Krumhansl-Schmuckler key estimate from the chroma vector, with the margin to the runner-up as confidence."""
    c = chroma_vector(x, rate)
    scores = []
    for tonic in range(12):
        for mode, prof in (("major", KS_MAJOR), ("minor", KS_MINOR)):
            r = np.corrcoef(c, np.roll(prof, tonic))[0, 1] if c.std() > 0 else 0.0
            scores.append((float(r), NOTE_NAMES[tonic], mode))
    scores.sort(reverse=True)
    return {"key": f"{scores[0][1]} {scores[0][2]}", "score": round(scores[0][0], 4),
            "margin": round(scores[0][0] - scores[1][0], 4), "runner_up": f"{scores[1][1]} {scores[1][2]}"}


def section_boundaries(x: np.ndarray, rate: int, min_len_s: float = 8.0, max_sections: int = 16) -> list[dict]:
    """Section boundaries from a Foote novelty curve over log-spectral frames (about 1 s resolution)."""
    hop = int(rate)  # 1 second frames
    n_fft = 4096
    frames = []
    m = mono(x)
    for s in range(0, max(1, len(m) - n_fft), hop):
        spec = np.abs(np.fft.rfft(m[s:s + n_fft] * np.hanning(len(m[s:s + n_fft]))))
        edges = np.unique(np.geomspace(2, len(spec) - 1, 25).astype(int))
        frames.append(np.log1p(np.array([spec[a:b].sum() for a, b in zip(edges[:-1], edges[1:])])))
    f = np.array(frames)
    if len(f) < 8:
        return []
    f = (f - f.mean(axis=0)) / (f.std(axis=0) + 1e-9)
    ssm = f @ f.T / f.shape[1]
    k = max(2, int(min_len_s / 2))
    half = np.r_[-np.ones(k), np.ones(k)]
    kern = np.outer(half, half)  # checkerboard: positive inside each half, negative across the boundary
    nov = np.zeros(len(f))
    for i in range(k, len(f) - k):
        nov[i] = np.sum(ssm[i - k:i + k, i - k:i + k] * kern)
    peaks, props = signal.find_peaks(nov, height=nov.max() * 0.35 if nov.max() > 0 else 1, distance=max(1, int(min_len_s)))
    pk = sorted(zip(peaks, props["peak_heights"]), key=lambda t: -t[1])[: max_sections - 1]
    return [{"time_s": round(float(i) * hop / rate, 2), "strength": round(float(h), 3)} for i, h in sorted(pk)]


def best_lag(a: np.ndarray, b: np.ndarray, max_lag: int) -> tuple[int, float]:
    """Lag (in samples) that best aligns b to a, and the normalized correlation there. Positive lag: b is late."""
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    nfft = 1 << int(math.ceil(math.log2(2 * n)))
    cc = np.fft.irfft(np.fft.rfft(a, nfft) * np.conj(np.fft.rfft(b, nfft)), nfft)
    cc = np.concatenate([cc[-max_lag:], cc[:max_lag + 1]])
    lags = np.arange(-max_lag, max_lag + 1)
    norm = math.sqrt(float(np.dot(a, a)) * float(np.dot(b, b))) or 1.0
    i = int(np.argmax(cc))
    return int(-lags[i]), float(cc[i] / norm)


def leakage_fraction(stem: np.ndarray, other: np.ndarray, rate: int, max_lag_s: float = 0.05) -> float:
    """Share of the stem's power that is linearly predictable from `other` (coherence weighted by stem power)."""
    a, b = mono(stem), mono(other)
    n = min(len(a), len(b))
    lag, _ = best_lag(a[:n], b[:n], int(max_lag_s * rate))
    b = np.roll(b[:n], -lag)
    f, coh = signal.coherence(a[:n], b, fs=rate, nperseg=min(4096, n))
    _, pxx = signal.welch(a[:n], fs=rate, nperseg=min(4096, n))
    total = float(np.sum(pxx))
    return float(np.sum(coh * pxx) / total) if total > 0 else 0.0


def band_overlap(a: np.ndarray, b: np.ndarray, rate: int, bands: dict, window_db: float = 12.0) -> dict:
    """Per-band masking risk 0 to 1: high when both signals have similar, non-negligible energy in the band."""
    ea, eb = band_energy_db(a, rate, bands), band_energy_db(b, rate, bands)
    out = {}
    for name in bands:
        both = min(ea[name], eb[name]) > -50.0
        out[name] = round(max(0.0, 1.0 - abs(ea[name] - eb[name]) / window_db) if both else 0.0, 3)
    return out
