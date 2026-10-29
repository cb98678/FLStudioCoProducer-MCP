from coproducer import synth


def test_known_signal(rig, wav):
    p = wav("a", synth.sine(440, 1.0, 0.5, channels=2))
    r = rig.call("measure_sample_peak", path=p)
    assert r.ok and r.value["peak_db"] == -6.02 and r.value["per_channel_db"] == [-6.02, -6.02]
    assert rig.call("measure_sample_peak", path=wav("z", synth.silence(0.5))).value["peak_db"] == -120.0


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_sample_peak", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_sample_peak", path="").error.code == "E_ARG"
