"""Synthesized drum one-shots and FX audio for sampler channels (editable-first: the sounds are samples, the beat is a pattern).

Every voice is deterministic for a given seed, mono unless noted, peak normalized to 1.0. Write them with
write_wav at a peak of about -1 dBFS and point sampler channels at the files.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 44100
METAL = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)


def _bp(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    return sosfilt(butter(order, [lo, min(hi, 20000)], btype="band", fs=SR, output="sos"), x)


def _hp(x: np.ndarray, f: float, order: int = 2) -> np.ndarray:
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def _lp(x: np.ndarray, f: float, order: int = 2) -> np.ndarray:
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def _fade(x: np.ndarray, ms: float = 20) -> np.ndarray:
    k = min(len(x), int(ms / 1000 * SR))
    x[-k:] *= np.linspace(1, 0, k)
    return x


def _nrm(x: np.ndarray) -> np.ndarray:
    return x / (np.max(np.abs(x)) + 1e-9)


def _noise(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(n)


def _metallic(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    return sum(np.sign(np.sin(2 * np.pi * f * t)) for f in METAL)


def kick(f0: float = 46, punch: float = 1.0, length: float = 0.45, drive: float = 1.8, seed: int = 11) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f0 + 120 * punch * np.exp(-t / 0.032)) / SR
    x = np.sin(ph) * np.exp(-t / 0.17) + 0.5 * np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.30)
    x += 0.35 * _bp(_noise(n, seed), 2000, 6000) * np.exp(-t / 0.004)
    x = np.tanh(drive * x)
    x[: int(0.0015 * SR)] *= np.linspace(0, 1, int(0.0015 * SR))
    return _nrm(_fade(x, 30))


def snare(body_hz: float = 185, decay: float = 0.11, length: float = 0.32, seed: int = 12) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (body_hz + 55 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.07)
    nz = _bp(_noise(n, seed), 1400, 9500) * np.exp(-t / decay)
    crack = _hp(_noise(n, seed + 1), 4000) * np.exp(-t / 0.02) * 0.5
    return _nrm(_fade(np.tanh(1.4 * (0.5 * body + 0.75 * nz + crack)), 40))


def clap(seed: int = 13) -> np.ndarray:
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, (d, g) in enumerate(((0, 1), (0.010, 0.9), (0.021, 0.9), (0.033, 1.1))):
        i = int(d * SR)
        x[i:] += _bp(_noise(n - i, seed + k), 900, 4200) * np.exp(-t[: n - i] / (0.012 if d < 0.03 else 0.09)) * g
    x += 0.25 * _bp(_noise(n, seed + 9), 700, 2500) * np.exp(-t / 0.16)
    return _nrm(_fade(np.tanh(1.2 * x), 40))


def hat(open_: bool = False, seed: int = 14) -> np.ndarray:
    n = int((0.38 if open_ else 0.07) * SR)
    t = np.arange(n) / SR
    x = _hp(_metallic(n) + 2.4 * _noise(n, seed), 7500) * np.exp(-t / (0.11 if open_ else 0.016))
    x[: int(0.0004 * SR)] *= np.linspace(0, 1, int(0.0004 * SR))
    return _nrm(_fade(x, 15))


def shaker(seed: int = 15) -> np.ndarray:
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    return _nrm(_fade(_bp(_noise(n, seed), 4500, 13000) * np.minimum(t / 0.012, 1) * np.exp(-t / 0.03), 10))


def rim(seed: int = 16) -> np.ndarray:
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1750 * t) * np.exp(-t / 0.006) + 0.5 * _bp(_noise(n, seed), 1500, 6000) * np.exp(-t / 0.01)
    return _nrm(_fade(x, 8))


def tom(f: float = 110, length: float = 0.4, seed: int = 17) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-t / 0.04))) / SR) * np.exp(-t / 0.12)
    x += 0.15 * _bp(_noise(n, seed), 800, 4000) * np.exp(-t / 0.01)
    return _nrm(_fade(np.tanh(1.3 * x), 30))


def crash(length: float = 2.4, seed: int = 18) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    x = _hp(0.35 * _metallic(n) + _noise(n, seed), 5000) * np.exp(-t / 0.55)
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return _nrm(_fade(x, 60))


def impact(length: float = 3.0, seed: int = 19) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(38 + 110 * np.exp(-t / 0.12)) / SR) * np.exp(-t / 0.9)
    x += 0.5 * _lp(_noise(n, seed), 500) * np.exp(-t / 0.35)
    return _nrm(_fade(np.tanh(1.5 * x), 80))


def sweep_noise(seconds: float, f0: float, f1: float, power: float = 2.0, width: float = 1.7, seed: int = 20) -> np.ndarray:
    """Stereo filtered-noise riser from f0 to f1 Hz with a power-law volume swell. Reverse it for a downlifter."""
    n = int(seconds * SR)
    blk, pre = 2048, 1024
    out = np.zeros((n, 2))
    for ch in range(2):
        x = _noise(n + pre * 2, seed + ch)
        for s in range(0, n, blk):
            fc = f0 * (f1 / f0) ** ((s + blk / 2) / n)
            y = _bp(x[s : s + blk + 2 * pre], max(fc / width, 30), min(fc * width, 19000))
            out[s : s + blk, ch] = y[pre : pre + min(blk, n - s)]
    return out * (np.linspace(0, 1, n) ** power)[:, None]


def tone_riser(seconds: float, f0: float, f1: float, power: float = 2.0) -> np.ndarray:
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ph = np.cumsum(2 * np.pi * f0 * (f1 / f0) ** (t / seconds)) / SR
    x = sum(np.sin(h * ph) / h for h in (1, 2, 3, 4))
    x = _lp(x, 6000) * (np.linspace(0, 1, n) ** power)
    return np.stack([x, np.roll(x, int(0.0007 * SR))], 1)


def reverse_crash(seconds: float, seed: int = 21) -> np.ndarray:
    x = crash(length=seconds * 1.8, seed=seed)[: int(seconds * SR)][::-1].copy()
    x *= np.linspace(0, 1, len(x)) ** 1.5
    return np.stack([x, np.roll(x, 30)], 1)


def sub_drop(seconds: float = 2.0, f0: float = 62.0, f1: float = 31.0) -> np.ndarray:
    """A sine falling from f0 to f1 Hz with an exponential fade: the sub hit under a drop's first kick (the demos' SFX Mega Sub, Sub Impact)."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / seconds)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    return _nrm(_fade(x, 40))


def noise_wash(seconds: float, f0: float = 1500.0, f1: float = 7000.0, seed: int = 22) -> np.ndarray:
    """A short band-passed noise swell that rises and falls (a wind or wash under a new phrase), stereo."""
    x = sweep_noise(seconds, f0, f1, power=1.0, seed=seed)
    n = len(x)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return x * env[:, None] / (np.max(np.abs(x)) + 1e-9)


def perc(seed: int = 23) -> np.ndarray:
    """A short tuned wood or conga hit (the demos' percussion layers)."""
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (420 * np.exp(-t * 18) + 260) * t) * np.exp(-t * 26)
    click = _bp(_noise(n, seed), 1800, 6000) * np.exp(-t * 160) * 0.4
    return _nrm(_fade(body + click, 10))


def ride(length: float = 1.6, seed: int = 24) -> np.ndarray:
    """A ride cymbal: a metallic ping over a long bright wash."""
    n = int(length * SR)
    t = np.arange(n) / SR
    wash = _hp(_noise(n, seed), 5000) * np.exp(-t * 2.4) * 0.5
    ping = sum(np.sin(2 * np.pi * f * t) for f in (3210.0, 4470.0, 5980.0)) * np.exp(-t * 6.0) * 0.25
    return _nrm(_fade(wash + ping, 60))


def sub_sine(hz: float, seconds: float, harmonics: tuple[float, float] = (0.22, 0.08)) -> np.ndarray:
    """A sub tone with light 2nd and 3rd harmonics. Used to match a synth patch to a generated sub (compare spectra, not by ear)."""
    t = np.arange(int(seconds * SR)) / SR
    ph = 2 * np.pi * hz * t
    return np.sin(ph) + harmonics[0] * np.sin(2 * ph) + harmonics[1] * np.sin(3 * ph)


def reese_pluck(f0: float = 55.0, length: float = 0.42, voices: int = 5, detune_cents: float = 14.0, drive: float = 2.6, seed: int = 31) -> np.ndarray:
    """A short detuned-saw bass pluck (stereo) for tech-house rolling bass: the note length does not matter because it decays on its own.

    Additive saws (every harmonic below 12 kHz), a low-pass that closes from about 18 times f0 to 3 times f0, tanh drive and a sine sub underneath.
    Tuned to f0 at sampler key 60, so a note on key 60 + n plays n semitones higher.
    """
    n = int(length * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    cut = f0 * (3.0 + 15.0 * np.exp(-t / 0.075))  # Hz, falls with the pluck
    out = np.zeros((n, 2))
    for v in range(voices):
        cents = (v - (voices - 1) / 2) * detune_cents * 2 / max(voices - 1, 1)
        f = f0 * 2 ** (cents / 1200)
        phase0 = rng.uniform(0, 2 * np.pi)
        sig = np.zeros(n)
        for k in range(1, int(12000 / f) + 1):
            gain = (1.0 / k) / np.sqrt(1.0 + (k * f / cut) ** 4)
            sig += gain * np.sin(2 * np.pi * k * f * t + k * phase0)
        pan = (v / max(voices - 1, 1)) * 2 - 1
        out[:, 0] += sig * (0.5 - 0.35 * pan)
        out[:, 1] += sig * (0.5 + 0.35 * pan)
    out = np.tanh(drive * out / voices * 1.8)
    sub = np.sin(2 * np.pi * f0 * t) * 0.9
    out = out * 0.75 + sub[:, None] * 0.55
    env = np.minimum(1.0, t / 0.003) * np.exp(-t / 0.22)
    out *= env[:, None]
    out /= np.max(np.abs(out)) + 1e-9
    k = int(0.04 * SR)
    out[-k:] *= np.linspace(1, 0, k)[:, None]
    return out


def rumble_kick(f0: float = 48.0, length: float = 1.4, tail_s: float = 0.9, tail_lp: float = 140.0, drive: float = 2.2, seed: int = 41) -> np.ndarray:
    """A techno kick with its rumble: the kick, then a low-passed, decaying noise and sine tail that reads as a reverb sent through a low-pass and
    drive (the usual rumble chain), all in one sample so the pattern stays editable. The tail sits under the next beats' kicks, so keep the pattern on
    the beat; the pump on the bass bus ducks it (style techno)."""
    n = int(length * SR)
    t = np.arange(n) / SR
    k = np.zeros(n)
    hit = kick(f0, punch=1.1, length=0.5, drive=drive, seed=seed)
    k[: len(hit)] = hit
    rng = np.random.default_rng(seed)
    tail = _lp(rng.standard_normal(n), tail_lp, 4) * 6 + 0.6 * np.sin(2 * np.pi * f0 * t)
    env = np.where(t < 0.06, 0.0, np.exp(-(t - 0.06) / (tail_s / 3))) * np.minimum(1, np.maximum(0, (t - 0.06) / 0.08))
    x = k + 0.55 * np.tanh(1.6 * tail * env)
    return _nrm(_fade(x, 60))


def bass_808(f0: float = 55.0, length: float = 1.8, punch: float = 0.7, drive: float = 1.5, decay_s: float = 1.1) -> np.ndarray:
    """A trap 808: a sine at f0 with a short pitch drop at the start, a long decay and soft saturation for the harmonics phones can play. Tuned to f0 at
    sampler key 60, like the reese, so bass lines use the same keys."""
    n = int(length * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + punch * np.exp(-t / 0.025))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay_s)
    x = np.tanh(drive * x) / np.tanh(drive)
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return _nrm(_fade(x, 40))


def growl(f0: float = 55.0, length: float = 0.9, bpm: float = 140.0, lfo_div: float = 2.0, index: float = 3.5, drive: float = 3.0, seed: int = 43) -> np.ndarray:
    """A dubstep mid-bass: FM (modulator at twice the note) with a low-pass that the tempo-synced LFO opens and closes (lfo_div per beat: 2 is an 8th
    wobble), then drive. Stereo, tuned to f0 at key 60. The sub stays a separate clean line (style dubstep), so this sample has its lows cut."""
    n = int(length * SR)
    t = np.arange(n) / SR
    lfo = 0.5 - 0.5 * np.cos(2 * np.pi * (bpm / 60.0 * lfo_div) * t)
    mod = np.sin(2 * np.pi * 2 * f0 * t) * index * (0.4 + 0.6 * lfo)
    car = np.sin(2 * np.pi * f0 * t + mod)
    rng = np.random.default_rng(seed)
    saw = sum(np.sin(2 * np.pi * k * f0 * 1.003 * t + rng.uniform(0, 6.3)) / k for k in range(1, 40))
    x = 0.6 * car + 0.4 * saw / 2
    out = np.zeros(n)
    blocks, zi = 64, np.zeros((1, 2))
    for i in range(0, n, blocks):  # a time-varying low-pass: new coefficients every 64 samples, the filter state carried across
        sos = butter(2, min(180 + 3800 * lfo[i], 15000), btype="low", fs=SR, output="sos")
        out[i : i + blocks], zi = sosfilt(sos, x[i : i + blocks], zi=zi)
    out = _hp(np.tanh(drive * out), 90, 2)
    env = np.minimum(1, t / 0.004) * np.where(t > length - 0.05, (length - t) / 0.05, 1.0)
    left = out * env
    right = np.roll(left, int(0.0007 * SR))
    return np.stack([left, right], 1) / (np.max(np.abs(left)) + 1e-9)


KIT = {"CP_Kick": kick, "CP_Snare": snare, "CP_Clap": clap, "CP_HatC": hat, "CP_HatO": lambda: hat(True), "CP_Shaker": shaker,
       "CP_Rim": rim, "CP_Tom": tom, "CP_Crash": crash, "CP_Perc": perc, "CP_Ride": ride}
VOICE_FNS = {"kick": kick, "snare": snare, "clap": clap, "hat": hat, "shaker": shaker, "rim": rim, "tom": tom, "crash": crash,
             "rumble_kick": rumble_kick, "bass_808": bass_808, "growl": growl, "reese_pluck": reese_pluck}


def voice(spec: dict) -> np.ndarray:
    """Render one voice from a style pack entry {"fn": name in VOICE_FNS, "args": {...}}."""
    if spec["fn"] not in VOICE_FNS:
        raise ValueError("unknown voice %r (known: %s)" % (spec["fn"], ", ".join(sorted(VOICE_FNS))))
    return VOICE_FNS[spec["fn"]](**spec.get("args", {}))


def write_wav(path: str | Path, x: np.ndarray, peak_db: float = -1.0) -> Path:
    """Peak-normalize to peak_db and write 16-bit PCM at 44.1 kHz."""
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)
    sf.write(str(path), x.astype(np.float32), SR, subtype="PCM_16")
    return Path(path)


def low_shelf_sos(fs: int, f0: float, gain_db: float, s: float = 0.8) -> np.ndarray:
    """RBJ cookbook low shelf (shelf slope s) as one second-order section."""
    a = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / fs
    alpha = np.sin(w0) / 2 * np.sqrt((a + 1 / a) * (1 / s - 1) + 2)
    c, r = np.cos(w0), 2 * np.sqrt(a) * alpha
    b = [a * ((a + 1) - (a - 1) * c + r), 2 * a * ((a - 1) - (a + 1) * c), a * ((a + 1) - (a - 1) * c - r)]
    d = [(a + 1) + (a - 1) * c + r, -2 * ((a - 1) + (a + 1) * c), (a + 1) + (a - 1) * c - r]
    return np.array([[b[0] / d[0], b[1] / d[0], b[2] / d[0], 1.0, d[1] / d[0], d[2] / d[0]]])


def shelve(path: str | Path, hz: float, db: float) -> Path:
    """Take low end out of a one-shot in place, without normalizing it again (so the cut is a cut, not a louder top). The house kick: 60 Hz,
    -4.5 dB, the person's choice by ear on The Curse of Curves club master (2026-10-26: "B is great")."""
    from scipy import signal as _sig
    x, rate = sf.read(str(path), always_2d=True)
    y = _sig.sosfilt(low_shelf_sos(rate, hz, db), x, axis=0)
    sf.write(str(path), y.astype(np.float32), rate, subtype="PCM_16")
    return Path(path)


def write_kit(folder: str | Path, spec: dict | None = None) -> dict[str, Path]:
    """Render the drum kit (nine voices, perc and ride) into folder as CP_*.wav. spec (a style pack's "kit") replaces voices by file name. Returns {name: path}."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    over = spec or {}
    return {name: write_wav(folder / (name + ".wav"), voice(over[name]) if name in over else fn()) for name, fn in KIT.items()}
