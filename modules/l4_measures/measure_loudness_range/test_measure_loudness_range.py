import numpy as np

from coproducer import synth


def test_known_signal(rig, wav):
    steady = rig.call("measure_loudness_range", path=wav("a", synth.sine(997, 8.0, 0.2))).value
    assert steady["lra_lu"] < 0.2
    x = np.vstack([synth.sine(997, 12.0, 0.05), synth.sine(997, 12.0, 0.5)])      # 20 dB step
    stepped = rig.call("measure_loudness_range", path=wav("b", x)).value
    assert 14 < stepped["lra_lu"] < 21


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_loudness_range", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_loudness_range", path="").error.code == "E_ARG"

    assert rig.call("measure_loudness_range", path=wav("s", synth.sine(997, 1.0))).error.code == "E_ARG"
