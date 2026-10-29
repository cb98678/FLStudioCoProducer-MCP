"""Tonal balance: band levels, reference profiles and the broad match EQ."""
import numpy as np
from scipy import signal

from coproducer import tonal

RATE = 44100


def _noise(tilt_db_per_oct: float, seconds: float = 8.0, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(int(RATE * seconds))
    spec = np.fft.rfft(w)
    f = np.fft.rfftfreq(len(w), 1 / RATE)
    f[0] = f[1]
    spec *= (f / 1000.0) ** (tilt_db_per_oct / 6.02)  # power slope in dB per octave (per Hz)
    x = np.fft.irfft(spec, len(w))
    return np.stack([x, x], axis=1) / np.abs(x).max() * 0.5


def test_band_levels_are_normalized_and_follow_the_tilt():
    flat, dark = tonal.band_levels(_noise(0.0), RATE), tonal.band_levels(_noise(-3.0), RATE)  # white rises 3 dB a band-octave, pink is flat
    assert len(flat) == len(tonal.CENTERS_HZ) == 29
    mid = [i for i, c in enumerate(tonal.CENTERS_HZ) if 100 <= c <= 10000]
    assert abs(np.mean([flat[i] for i in mid])) < 0.05
    hi = tonal.CENTERS_HZ.index(8000.0)
    assert dark[hi] < flat[hi] - 6 and abs(dark[hi]) < 1.0                                             # a darker track has less top end at equal mid level


def test_profile_spread_and_deviation():
    a, b = tonal.band_levels(_noise(-3.0, seed=1), RATE), tonal.band_levels(_noise(-3.2, seed=2), RATE)
    prof = tonal.profile([a, b])
    assert prof["tracks"] == 2 and min(prof["spread_db"]) >= 1.0
    inside = tonal.deviation(a, prof)
    assert inside["outside"] == 0
    bright = tonal.deviation(tonal.band_levels(_noise(0.0), RATE), prof)
    assert bright["outside"] > 4 and bright["beyond_db"][tonal.CENTERS_HZ.index(8000.0)] > 3 and bright["beyond_db"][2] < -3


def test_match_moves_a_track_toward_the_profile_and_leaves_the_sub_alone():
    prof = tonal.profile([tonal.band_levels(_noise(-3.0, seed=s), RATE) for s in (1, 2, 3)])
    x = _noise(0.0)
    own = tonal.band_levels(x, RATE)
    g = tonal.match_gains(own, prof)
    assert max(abs(v) for v in g) <= 4.0
    assert g[0] == 0.0                                                         # 25 Hz: below the 35 Hz bound
    assert g[tonal.CENTERS_HZ.index(5039.7)] < -1.0                            # highs come down
    y = tonal.apply_eq(x, RATE, g)
    assert y.shape == x.shape
    before, after = tonal.deviation(own, prof)["rms_db"], tonal.deviation(tonal.band_levels(y, RATE), prof)["rms_db"]
    assert after < before * 0.75


def test_flat_gains_are_transparent_and_in_time():
    x = _noise(-3.0, seconds=2.0)
    y = tonal.apply_eq(x, RATE, [0.0] * 29)
    assert np.max(np.abs(y - x)) < 1e-3
    imp = np.zeros((RATE, 2))
    imp[RATE // 2] = 1.0
    z = tonal.apply_eq(imp, RATE, [3.0 if 200 < c < 2000 else 0.0 for c in tonal.CENTERS_HZ])
    assert int(np.argmax(np.abs(z[:, 0]))) == RATE // 2                       # linear phase, delay removed
    assert signal.welch(z[:, 0], RATE)[1].max() > 0


def test_master_prepare_removes_dc_and_cuts_a_dead_tail():
    from coproducer import mastering
    x = _noise(-3.0, seconds=6.0) * 0.5
    x[int(4 * RATE):] = 0.0
    x[:, 0] -= 0.0167                                                          # a held offset to the end, as a stuck filter state left it
    x[:, 1] += 0.0097
    y, info = mastering.prepare(x, RATE)
    assert info["dc_before"][0] < -0.01 and abs(y.mean(axis=0)).max() < 1e-3
    assert 1.5 < info["trimmed_s"] < 1.8 and abs(y[-1]).max() < 1e-6        # 2 s of DC tail cut to a quarter second after the sound
    z, info2 = mastering.prepare(_noise(-3.0, seconds=3.0), RATE)
    assert info2["trimmed_s"] == 0.0 and len(z) == 3 * RATE


def test_master_prepare_makes_the_lows_mono():
    from coproducer import mastering
    t = np.arange(4 * RATE) / RATE
    low, high = np.sin(2 * np.pi * 50 * t), np.sin(2 * np.pi * 2000 * t) * 0.3
    x = np.stack([low + high, -low + high], axis=1) * 0.4                      # 50 Hz fully out of phase: all side; 2 kHz in the middle
    y, info = mastering.prepare(x, RATE, mono_below_hz=120.0)
    side_low = np.sqrt(np.mean(((y[:, 0] - y[:, 1]) / 2)[RATE:-RATE] ** 2))
    assert info["mono_below_hz"] == 120.0 and side_low < 0.02                  # the 50 Hz side is gone (it was 0.28 RMS)
    z, _ = mastering.prepare(np.stack([high, high], axis=1), RATE, mono_below_hz=120.0)
    assert np.allclose(z[RATE:-RATE], high[RATE:-RATE, None], atol=1e-3)       # mid content passes untouched
