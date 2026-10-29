from coproducer import synth


def test_overlapping_and_separate_sources(rig, wav):
    a, b = wav("a", synth.sine(100, 2.0)), wav("b", synth.sine(110, 2.0, 0.8))
    same = rig.call("measure_masking_overlap", path_a=a, path_b=b).value
    assert same["bands"]["bass"] > 0.7 and same["worst"][0]["band"] == "bass"
    c = wav("c", synth.sine(5000, 2.0))
    apart = rig.call("measure_masking_overlap", path_a=a, path_b=c).value
    assert apart["bands"]["bass"] == 0.0 and apart["worst"] == []


def test_failures(rig, wav, tmp_path):
    a = wav("a", synth.sine(100, 1.0))
    assert rig.call("measure_masking_overlap", path_a=a, path_b=str(tmp_path / "no.wav")).error.code == "E_IO"
    assert rig.call("measure_masking_overlap", path_a=a, path_b=wav("r", synth.sine(100, 1.0, rate=44100), 44100)).error.code == "E_ARG"
