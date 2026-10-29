from coproducer import synth


def test_measures_known_leakage(rig, wav):
    bleed = synth.noise(6.0, 0.1, channels=1, seed=7)
    clean = synth.sine(440, 6.0, 0.3)
    stem = wav("stem", clean + 0.5 * bleed)
    other = wav("other", bleed)
    r = rig.call("detect_leakage", path=stem, others=[other, wav("unrelated", synth.noise(6.0, 0.1, channels=1, seed=99))])
    expected = (0.25 * 0.01) / (0.3 ** 2 / 2 + 0.25 * 0.01)       # leaked power over total stem power
    assert r.ok and abs(r.value["leakage"][0]["share"] - expected) < 0.03
    assert r.value["leakage"][1]["share"] < 0.03 and r.value["worst_share"] == r.value["leakage"][0]["share"]


def test_failures(rig, wav, tmp_path):
    a = wav("a", synth.sine(440, 1.0))
    assert rig.call("detect_leakage", path=a, others=[str(tmp_path / "no.wav")]).error.code == "E_IO"
    assert rig.call("detect_leakage", path=a, others=[wav("r", synth.sine(440, 1.0, rate=44100), 44100)]).error.code == "E_ARG"
    assert rig.call("detect_leakage", path=a, others=[]).error.code == "E_ARG"
