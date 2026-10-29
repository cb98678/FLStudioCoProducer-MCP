from coproducer import synth


def test_known_signal(rig, wav):
    r = rig.call("measure_rms", path=wav("a", synth.sine(440, 1.0, 1.0, channels=2)))
    assert r.ok and r.value["rms_db"] == -3.01 and r.value["per_channel_db"] == [-3.01, -3.01]


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_rms", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_rms", path="").error.code == "E_ARG"
