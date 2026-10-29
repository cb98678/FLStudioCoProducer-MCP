import numpy as np
from scipy import signal

from coproducer import synth


def _word(rate=16000):
    t = np.arange(int(1.2 * rate)) / rate
    x = np.zeros_like(t)
    v = (t > 0.1) & (t < 0.4)
    x[v] = 0.2 * np.sin(2 * np.pi * 220 * t[v]) + 0.1 * np.sin(2 * np.pi * 440 * t[v])
    q = (t >= 0.4) & (t < 0.62)
    x[q] = 0.004 * np.sin(2 * np.pi * 220 * t[q])
    h = (t >= 0.62) & (t < 0.69)
    x[h] = signal.sosfilt(signal.butter(4, 5000, "hp", fs=rate, output="sos"), np.random.default_rng(3).standard_normal(int(h.sum())) * 0.08)
    n = t >= 0.72
    x[n] = 0.2 * np.sin(2 * np.pi * 180 * t[n])
    return x.astype("float32"), rate


def test_finds_the_hiss_after_a_dip(rig, wav):
    x, rate = _word()
    r = rig.call("find_final_s_end", path=wav("w", x, rate), end_s=0.42).value
    assert r["found"] and 0.68 <= r["end_s"] <= 0.74
    assert rig.call("find_final_s_end", path=wav("w2", x, rate), end_s=0.1).value["end_s"] <= 0.42  # nothing hissy right after the start


def test_failures(rig, wav, tmp_path):
    assert rig.call("find_final_s_end", path=str(tmp_path / "missing.wav"), end_s=1.0).error.code == "E_IO"
    assert rig.call("find_final_s_end", path="", end_s=1.0).error.code == "E_ARG"
    assert rig.call("find_final_s_end", path=wav("t", synth.sine(220, 0.5, 0.5)), end_s=5.0).error.code == "E_ARG"
