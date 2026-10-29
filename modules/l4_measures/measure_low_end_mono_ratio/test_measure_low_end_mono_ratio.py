import numpy as np

from coproducer import synth


def test_known_signal(rig, wav):
    mono_bass_wide_highs = np.hstack([synth.sine(60, 2.0) + synth.sine(5000, 2.0, 0.3),
                                      synth.sine(60, 2.0) - synth.sine(5000, 2.0, 0.3)])
    good = rig.call("measure_low_end_mono_ratio", path=wav("a", mono_bass_wide_highs)).value
    assert good["mono_below_cutoff"] is True and good["side_over_mid_db"] < -40
    wide_bass = np.hstack([synth.sine(60, 2.0), -synth.sine(60, 2.0)])
    bad = rig.call("measure_low_end_mono_ratio", path=wav("b", wide_bass)).value
    assert bad["mono_below_cutoff"] is False and bad["side_over_mid_db"] > 20


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_low_end_mono_ratio", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_low_end_mono_ratio", path="").error.code == "E_ARG"

    assert rig.call("measure_low_end_mono_ratio", path=wav("m", synth.sine(60, 0.5))).error.code == "E_ARG"
