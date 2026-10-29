from coproducer import synth


def test_known_signal(rig, wav):
    assert abs(rig.call("measure_integrated_loudness", path=wav("a", synth.sine(997, 5.0, 1.0))).value["lufs"] + 3.01) < 0.05
    assert abs(rig.call("measure_integrated_loudness", path=wav("b", synth.sine(997, 5.0, 0.1, channels=2))).value["lufs"] + 20.0) < 0.05
    assert rig.call("measure_integrated_loudness", path=wav("c", synth.silence(2.0))).value["lufs"] == -120.0


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_integrated_loudness", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_integrated_loudness", path="").error.code == "E_ARG"

    assert rig.call("measure_integrated_loudness", path=wav("s", synth.sine(997, 0.1))).error.code == "E_ARG"
