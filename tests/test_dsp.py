"""DSP library checks against analytic values and against pyloudnorm."""
import math

import numpy as np
import pyloudnorm as pyln
import pytest

from coproducer import dsp

RATE = 48000


def sine(freq, seconds=3.0, amp=1.0, rate=RATE, phase=0.0, channels=1):
    t = np.arange(int(seconds * rate)) / rate
    s = amp * np.sin(2 * np.pi * freq * t + phase)
    return np.tile(s[:, None], (1, channels))


def test_db_helpers():
    assert dsp.db(1.0) == 0.0 and abs(dsp.db(0.5) + 6.0206) < 1e-3 and dsp.db(0.0) == dsp.FLOOR_DB
    assert abs(dsp.power_db(0.5) + 3.0103) < 1e-3


def test_k_weighting_coefficients_match_the_published_48k_values():
    # ITU-R BS.1770-4, Table 1 and Table 2 (48 kHz)
    b, a = dsp._biquad_shelf(48000)
    assert np.allclose(b, [1.53512485958697, -2.69169618940638, 1.19839281085285], atol=1e-8)
    assert np.allclose(a, [1.0, -1.69065929318241, 0.73248077421585], atol=1e-8)
    b, a = dsp._biquad_highpass(48000)
    assert np.allclose(b, [1.0, -2.0, 1.0]) and np.allclose(a, [1.0, -1.99004745483398, 0.99007225036621], atol=1e-8)


def test_k_weighted_loudness_agrees_with_pyloudnorm():
    rng = np.random.default_rng(1)
    x = rng.normal(0, 0.1, (RATE * 6, 2))
    ours = dsp.window_loudness(x, RATE, 6.0, 1.0)[1][0]
    assert abs(ours - pyln.Meter(RATE).integrated_loudness(x)) < 0.1  # pyloudnorm uses RBJ approximations of the ITU filters


@pytest.mark.parametrize("rate", [44100, 48000, 96000])
def test_integrated_loudness_reference_values(rate):
    meter = pyln.Meter(rate)
    x = sine(997, 5.0, 1.0, rate)
    assert abs(meter.integrated_loudness(x) - (-3.01)) < 0.05   # BS.1770: full-scale mono sine is -3.01 LUFS
    st = sine(997, 5.0, 0.1, rate, channels=2)       # -20 dBFS in both channels
    assert abs(meter.integrated_loudness(st) - (-20.0)) < 0.05
    assert abs(dsp.window_loudness(st, rate, 3.0, 1.0)[1].mean() - (-20.0)) < 0.05


def test_window_loudness_agrees_with_pyloudnorm_on_steady_signal():
    rng = np.random.default_rng(2)
    x = rng.normal(0, 0.05, (RATE * 8, 2))
    t, l = dsp.window_loudness(x, RATE, 3.0, 1.0)
    assert abs(float(np.mean(l)) - pyln.Meter(RATE).integrated_loudness(x)) < 0.15
    assert len(t) == 6 and t[1] - t[0] == 1.0


def test_loudness_range_of_steady_and_stepped_signals():
    assert dsp.loudness_range(np.full(100, -20.0))[0] == 0.0
    stepped = np.r_[np.full(50, -30.0), np.full(50, -20.0)]
    assert abs(dsp.loudness_range(stepped)[0] - 10.0) < 0.5
    assert dsp.loudness_range(np.full(10, -90.0)) == (0.0, dsp.FLOOR_DB, dsp.FLOOR_DB)


def test_true_peak_finds_intersample_peaks():
    # a sine at fs/4 sampled 45 degrees off its crest: every sample is 0.707, the true peak is 1.0
    x = sine(RATE / 4, 1.0, 1.0, phase=math.pi / 4)
    assert abs(np.max(np.abs(x)) - 0.7071) < 1e-3
    assert abs(dsp.true_peak(x, RATE) - 1.0) < 0.02


def test_correlation_and_zero_signal():
    a = sine(440, 1.0)[:, 0]
    assert abs(dsp.correlation(a, a) - 1) < 1e-9 and abs(dsp.correlation(a, -a) + 1) < 1e-9
    assert dsp.correlation(a, np.zeros_like(a)) == 0.0


def test_band_energy_and_centroid():
    x = sine(100, 2.0) + sine(5000, 2.0) * 0.1
    e = dsp.band_energy_db(x, RATE, dsp.DEFAULT_BANDS)
    assert e["bass"] > -1.0 and -22 < e["presence"] < -18 and e["air"] < -60
    assert 100 < dsp.spectral_centroid(x, RATE) < 400


def _clicks(bpm, seconds=20.0, rate=22050):
    x = np.zeros(int(seconds * rate))
    rng = np.random.default_rng(0)
    step = rate * 60.0 / bpm
    for i in range(int(seconds * bpm / 60)):
        s = int(i * step)
        burst = rng.normal(0, 1, 800) * np.exp(-np.arange(800) / 120)
        x[s:s + 800] += burst[: len(x[s:s + 800])]
    return x[:, None]


@pytest.mark.parametrize("bpm", [90, 128, 140, 174])
def test_tempo_estimate(bpm):
    cands = dsp.estimate_tempo(_clicks(bpm), 22050)
    assert cands, "no candidates"
    got = [c["bpm"] for c in cands[:3]]
    assert any(abs(g - bpm) < 1.5 or abs(g - bpm / 2) < 1.0 or abs(g - bpm * 2) < 2.0 for g in got), (bpm, got)
    assert any(abs(g - bpm) < 1.5 for g in [c["bpm"] for c in cands]), (bpm, cands)


def _chord(freqs, seconds=2.0, rate=22050):
    return sum(sine(f, seconds, 1.0 / len(freqs), rate) for f in freqs)


def _note(name, octave=3):
    return 440.0 * 2 ** ((dsp.NOTE_NAMES.index(name) - 9 + 12 * (octave - 4)) / 12)


@pytest.mark.parametrize("tonic,mode,scale", [
    ("C", "major", [0, 2, 4, 5, 7, 9, 11]), ("A", "minor", [0, 2, 3, 5, 7, 8, 10]),
    ("F#", "minor", [0, 2, 3, 5, 7, 8, 10]), ("D#", "major", [0, 2, 4, 5, 7, 9, 11])])
def test_key_estimate(tonic, mode, scale):
    base = dsp.NOTE_NAMES.index(tonic)
    weights = {0: 3.0, 4 if mode == "major" else 3: 1.5, 7: 2.0}
    x = 0
    for degree in scale:
        name = dsp.NOTE_NAMES[(base + degree) % 12]
        x = x + weights.get(degree, 0.6) * _chord([_note(name, 3), _note(name, 4)], 1.0, 22050)
    r = dsp.estimate_key(x / np.max(np.abs(x)), 22050)
    assert r["key"] == f"{tonic} {mode}", r


def test_section_boundaries_found_in_synthetic_song():
    rate = 22050
    rng = np.random.default_rng(3)
    a = sine(220, 20.0, 0.5, rate)
    b = rng.normal(0, 0.3, (20 * rate, 1))
    c = sine(1760, 20.0, 0.5, rate)
    secs = dsp.section_boundaries(np.vstack([a, b, c]), rate)
    times = [s["time_s"] for s in secs]
    assert any(abs(t - 20) < 2.5 for t in times) and any(abs(t - 40) < 2.5 for t in times), times


def test_best_lag_recovers_delay():
    rng = np.random.default_rng(4)
    a = rng.normal(0, 1, 20000)
    b = np.r_[np.zeros(137), a][:20000]
    lag, c = dsp.best_lag(a, b, 500)
    assert lag == 137 and c > 0.9
    lag2, _ = dsp.best_lag(b, a, 500)
    assert lag2 == -137


def test_integrated_loudness_with_gating_matches_pyloudnorm():
    rng = np.random.default_rng(5)
    loud = rng.normal(0, 0.1, (RATE * 10, 2))
    quiet = rng.normal(0, 0.001, (RATE * 10, 2))          # about 40 dB lower: gated out
    both = np.vstack([loud, quiet])
    ours = dsp.integrated_loudness(both, RATE)
    assert abs(ours - pyln.Meter(RATE).integrated_loudness(both)) < 0.1
    assert abs(ours - dsp.integrated_loudness(loud, RATE)) < 0.15  # transition blocks pass the gate
    assert abs(dsp.integrated_loudness(sine(997, 5.0, 1.0), RATE) + 3.01) < 0.05
    assert dsp.integrated_loudness(np.zeros((RATE, 2)), RATE) == dsp.FLOOR_DB
    with pytest.raises(ValueError):
        dsp.integrated_loudness(np.zeros((100, 2)), RATE)
