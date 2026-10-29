import numpy as np
from scipy import signal

from coproducer import synth


def _chop(tail="none", cut=False, rate=44100):
    body = synth.sine(220, 0.5, 0.5, rate)[:, 0]
    n = len(body)
    fade = np.linspace(0, 1, int(0.005 * rate))
    body[: len(fade)] *= fade
    if not cut:
        out = np.linspace(1, 0, int(0.2 * rate))  # decays well below -24 dB before the end
        body[-len(out) :] *= out**3
    parts = [body]
    if tail == "hiss":
        rng = np.random.default_rng(2)
        h = signal.sosfilt(signal.butter(4, 5000, "hp", fs=rate, output="sos"), rng.standard_normal(int(0.1 * rate)) * 0.2)
        h[: int(0.01 * rate)] *= np.linspace(0, 1, int(0.01 * rate))
        h[-int(0.035 * rate) :] *= np.linspace(1, 0, int(0.035 * rate))
        parts.append(h)
    elif cut:
        body[-int(0.035 * rate) :] *= np.linspace(1, 0, int(0.035 * rate))
    return np.concatenate(parts)[: n + (len(parts[-1]) if tail == "hiss" else 0)]


def test_clean_and_cut_chops(rig, wav):
    clean = rig.call("check_vocal_edges", path=wav("clean", _chop())).value
    assert not clean["abrupt_end"] and not clean["ends_on_hiss"]
    cut = rig.call("check_vocal_edges", path=wav("cut", _chop(cut=True))).value
    assert cut["abrupt_end"]
    hiss = rig.call("check_vocal_edges", path=wav("hiss", _chop(tail="hiss"))).value
    assert hiss["ends_on_hiss"]


def test_failures(rig, wav, tmp_path):
    assert rig.call("check_vocal_edges", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("check_vocal_edges", path="").error.code == "E_ARG"
    assert rig.call("check_vocal_edges", path=wav("tiny", synth.sine(220, 0.05, 0.5))).error.code == "E_ARG"
