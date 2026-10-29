"""vocalfx: each stage does what it says and the chain keeps the length."""
import numpy as np

from coproducer import vocalfx as V

SR = 48000


def _speechlike(seconds=3.0, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    env = (np.sin(2 * np.pi * 2.5 * t) > 0).astype(float) * 0.5 + 0.02
    f0 = 120
    x = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 20)) * env * 0.3
    return x + rng.standard_normal(len(t)) * 0.003 + 0.05 * np.sin(2 * np.pi * 30 * t)


def test_hpf_removes_rumble_and_keeps_length():
    t = np.arange(SR) / SR
    x = np.sin(2 * np.pi * 30 * t) + np.sin(2 * np.pi * 1000 * t)
    y = V.hpf(x, SR, 100)
    assert len(y) == len(x)
    X = np.abs(np.fft.rfft(y))
    f = np.fft.rfftfreq(len(y), 1 / SR)
    assert X[np.argmin(abs(f - 30))] < 0.05 * X[np.argmin(abs(f - 1000))]


def test_tone_boost_and_cut_land_where_asked():
    rng = np.random.default_rng(0)
    x = rng.standard_normal(SR * 2)
    y = V.tone(x, SR, [("peak", 3000.0, 6.0, 1.0)])
    f = np.fft.rfftfreq(len(x), 1 / SR)
    gx = np.abs(np.fft.rfft(x)); gy = np.abs(np.fft.rfft(y))
    sel = (f > 2800) & (f < 3200)
    gain = 20 * np.log10(np.mean(gy[sel]) / np.mean(gx[sel]))
    assert 4.5 < gain < 7.0
    far = (f > 200) & (f < 400)
    assert abs(20 * np.log10(np.mean(gy[far]) / np.mean(gx[far]))) < 0.7


def test_compress_narrows_the_loud_to_soft_range_and_keeps_level():
    t = np.arange(2 * SR) / SR
    carrier = np.sin(2 * np.pi * 440 * t)
    amp = np.where(t < 1.0, 0.5, 0.05)                 # a 20 dB step: loud then soft
    x = carrier * amp
    y = V.compress(x, SR, thresh_db=-40, ratio=4)
    rms = lambda a, i0, i1: np.sqrt(np.mean(a[int(i0 * SR):int(i1 * SR)] ** 2))
    step_in = 20 * np.log10(rms(x, 0.3, 0.9) / rms(x, 1.3, 1.9))
    step_out = 20 * np.log10(rms(y, 0.3, 0.9) / rms(y, 1.3, 1.9))
    assert step_out < 0.6 * step_in
    assert len(y) == len(x)


def test_deess_only_touches_sibilant_band():
    t = np.arange(SR) / SR
    voice = 0.2 * np.sin(2 * np.pi * 300 * t)
    ess = 0.2 * np.sin(2 * np.pi * 7000 * t) * (t > 0.5)
    y = V.deess(voice + ess, SR, thresh_db=-30, ratio=4)
    spec = lambda a, hz: np.abs(np.fft.rfft(a))[int(hz * len(a) / SR)]
    assert spec(y, 7000) < 0.7 * spec(voice + ess, 7000)
    assert spec(y, 300) > 0.95 * spec(voice + ess, 300)


def test_clean_vocal_same_length_finite_and_under_ceiling():
    x = _speechlike()
    y = V.clean_vocal(x, SR, nr_amount=0.0)
    assert len(y) == len(x) and np.all(np.isfinite(y))
    assert np.max(abs(y)) <= 10 ** (-1.0 / 20) + 1e-6
    X = np.abs(np.fft.rfft(y)); f = np.fft.rfftfreq(len(y), 1 / SR)
    assert X[np.argmin(abs(f - 30))] < 0.2 * X[np.argmin(abs(f - 360))]
