import numpy as np

from coproducer import synth


def test_finds_regions(rig, wav):
    x = np.vstack([synth.sine(440, 1.0, 0.5), synth.silence(2.0), synth.sine(440, 1.0, 0.5)])
    r = rig.call("detect_silence", path=wav("a", x))
    assert r.ok and r.value["regions"] == [{"start_s": 1.0, "end_s": 3.0}] and r.value["silent_fraction"] == 0.5
    assert r.value["mostly_silent"] is False
    quiet = rig.call("detect_silence", path=wav("b", synth.silence(2.0))).value
    assert quiet["mostly_silent"] is True and quiet["silent_fraction"] == 1.0
    short = rig.call("detect_silence", path=wav("c", np.vstack([synth.sine(440, 1.0), synth.silence(0.2), synth.sine(440, 1.0)])))
    assert short.value["regions"] == []


def test_failures(rig, tmp_path):
    assert rig.call("detect_silence", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("detect_silence", path="x", threshold_db=5).error.code == "E_ARG"
