import math

from coproducer import synth


def test_known_signal(rig, wav):
    # a fs/4 sine 45 degrees off its crest hides a 1.2 peak between samples that all read 0.85
    p = wav("a", synth.sine(12000, 1.0, 1.2, phase=math.pi / 4))
    r = rig.call("measure_true_peak", path=p)
    assert r.ok and abs(r.value["sample_peak_db"] + 1.43) < 0.05 and abs(r.value["true_peak_dbtp"] - 1.58) < 0.25  # the hard start of the sine adds a little filter ringing
    assert r.value["intersample_over"] is True
    quiet = rig.call("measure_true_peak", path=wav("q", synth.sine(1000, 1.0, 0.5))).value
    assert quiet["intersample_over"] is False and abs(quiet["true_peak_dbtp"] + 6.02) < 0.1


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_true_peak", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_true_peak", path="").error.code == "E_ARG"
