import numpy as np

from coproducer import synth


def test_known_signal(rig, wav):
    x = np.vstack([synth.sine(997, 6.0, 0.1), synth.sine(997, 6.0, 0.4)])
    r = rig.call("measure_short_term_loudness", path=wav("a", x))
    assert r.ok and len(r.value["lufs"]) == 10
    assert abs(r.value["max_lufs"] - r.value["min_lufs"] - 12.04) < 0.2 and abs(r.value["min_lufs"] + 23.0) < 0.2


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_short_term_loudness", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_short_term_loudness", path="").error.code == "E_ARG"

    assert rig.call("measure_short_term_loudness", path=wav("s", synth.sine(997, 1.0))).error.code == "E_ARG"
