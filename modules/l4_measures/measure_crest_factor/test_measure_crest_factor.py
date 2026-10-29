from coproducer import synth


def test_known_signal(rig, wav):
    assert rig.call("measure_crest_factor", path=wav("a", synth.sine(440, 1.0, 0.7))).value["crest_db"] == 3.01
    noisy = rig.call("measure_crest_factor", path=wav("n", synth.noise(2.0, 0.1))).value["crest_db"]
    assert 10 < noisy < 16


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_crest_factor", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_crest_factor", path="").error.code == "E_ARG"
