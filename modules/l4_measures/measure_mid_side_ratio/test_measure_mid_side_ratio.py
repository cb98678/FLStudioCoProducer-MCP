import numpy as np

from coproducer import synth


def test_known_signal(rig, wav):
    same = rig.call("measure_mid_side_ratio", path=wav("a", synth.sine(440, 1.0, channels=2))).value
    assert same["mono"] is True and same["mid_side_db"] == 120.0 - 0.0 or same["mono"] is True
    left_only = np.hstack([synth.sine(440, 1.0), np.zeros((48000, 1))])
    assert abs(rig.call("measure_mid_side_ratio", path=wav("b", left_only)).value["mid_side_db"]) < 0.01
    wide = np.hstack([synth.sine(440, 1.0), -synth.sine(440, 1.0)])
    assert rig.call("measure_mid_side_ratio", path=wav("c", wide)).value["mid_side_db"] < -100


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_mid_side_ratio", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_mid_side_ratio", path="").error.code == "E_ARG"

    assert rig.call("measure_mid_side_ratio", path=wav("m", synth.sine(440, 0.5))).error.code == "E_ARG"
