import numpy as np

from coproducer import synth


def test_known_signal(rig, wav):
    assert rig.call("measure_stereo_correlation", path=wav("a", synth.sine(440, 1.0, channels=2))).value["correlation"] == 1.0
    inv = np.hstack([synth.sine(440, 1.0), -synth.sine(440, 1.0)])
    r = rig.call("measure_stereo_correlation", path=wav("b", inv)).value
    assert r["correlation"] == -1.0 and r["mono_compatible"] is False
    assert abs(rig.call("measure_stereo_correlation", path=wav("c", synth.noise(2.0))).value["correlation"]) < 0.05


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_stereo_correlation", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_stereo_correlation", path="").error.code == "E_ARG"

    assert rig.call("measure_stereo_correlation", path=wav("m", synth.sine(440, 0.5))).error.code == "E_ARG"
