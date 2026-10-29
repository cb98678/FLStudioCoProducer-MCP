import numpy as np
from coproducer import synth


def test_known_signal(rig, wav):
    p = wav("a", synth.sine(440, 1.0, 0.5, channels=2))
    r = rig.call("read_audio_file", path=p)
    assert r.ok and r.value["rate"] == 48000 and r.value["channels"] == 2 and r.value["seconds"] == 1.0
    assert abs(np.max(r.value["samples"]) - 0.5) < 1e-6
    assert rig.call("read_audio_file", path=p, max_seconds=0.25).value["seconds"] == 0.25


def test_failures(rig, wav, tmp_path):
    assert rig.call("read_audio_file", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("read_audio_file", path="").error.code == "E_ARG"
