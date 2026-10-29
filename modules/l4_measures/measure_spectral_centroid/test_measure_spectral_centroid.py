from coproducer import synth


def test_known_signal(rig, wav):
    low = rig.call("measure_spectral_centroid", path=wav("a", synth.sine(200, 2.0))).value["centroid_hz"]
    high = rig.call("measure_spectral_centroid", path=wav("b", synth.sine(4000, 2.0))).value["centroid_hz"]
    assert abs(low - 200) < 15 and abs(high - 4000) < 60


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_spectral_centroid", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_spectral_centroid", path="").error.code == "E_ARG"
