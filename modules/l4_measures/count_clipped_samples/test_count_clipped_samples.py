import numpy as np

from coproducer import synth


def test_known_signal(rig, wav):
    x = np.clip(synth.sine(440, 1.0, 2.0), -1, 1)                 # a hard-clipped sine
    r = rig.call("count_clipped_samples", path=wav("a", x)).value
    assert r["clipped_samples"] > 10000 and r["longest_run"] > 10
    clean = rig.call("count_clipped_samples", path=wav("b", synth.sine(440, 1.0, 0.5))).value
    assert clean == {"clipped_samples": 0, "longest_run": 0, "clipped_fraction": 0.0}


def test_failures(rig, wav, tmp_path):
    assert rig.call("count_clipped_samples", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("count_clipped_samples", path="").error.code == "E_ARG"
