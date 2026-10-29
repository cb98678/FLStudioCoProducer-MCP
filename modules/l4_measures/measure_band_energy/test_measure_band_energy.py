from coproducer import synth


def test_known_signal(rig, wav):
    x = synth.sine(100, 2.0) + 0.1 * synth.sine(5000, 2.0)
    r = rig.call("measure_band_energy", path=wav("a", x))
    assert r.ok and r.value["bass"] > -1 and -22 < r.value["presence"] < -18 and r.value["air"] < -60
    custom = rig.call("measure_band_energy", path=wav("b", x), bands={"low": [0, 1000], "high": [1000, 10000]}).value
    assert set(custom) == {"low", "high"} and custom["low"] > -1


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_band_energy", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_band_energy", path="").error.code == "E_ARG"
