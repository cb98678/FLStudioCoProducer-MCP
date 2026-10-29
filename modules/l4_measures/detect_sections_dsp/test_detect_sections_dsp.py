import numpy as np

from coproducer import synth


def test_finds_boundaries(rig, wav):
    rate = 22050
    x = np.vstack([synth.sine(220, 20.0, 0.5, rate), synth.noise(20.0, 0.3, rate, 1), synth.sine(1760, 20.0, 0.5, rate)])
    r = rig.call("detect_sections_dsp", path=wav("a", x, rate))
    times = [b["time_s"] for b in r.value["boundaries"]]
    assert r.ok and any(abs(t - 20) < 2.5 for t in times) and any(abs(t - 40) < 2.5 for t in times)


def test_failures(rig, wav, tmp_path):
    assert rig.call("detect_sections_dsp", path=str(tmp_path / "no.wav")).error.code == "E_IO"
    assert rig.call("detect_sections_dsp", path=wav("s", synth.sine(220, 5.0))).error.code == "E_ARG"
