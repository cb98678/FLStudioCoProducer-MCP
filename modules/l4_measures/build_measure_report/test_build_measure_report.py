from coproducer import synth


def test_report_has_every_section(rig, wav):
    r = rig.call("build_measure_report", path=wav("a", synth.drum_loop(140, bars=4)))
    assert r.ok
    assert set(r.value) >= {"sample_peak", "true_peak", "rms", "crest", "loudness", "range", "bands", "centroid",
                            "clipping", "silence", "correlation", "mid_side", "low_end_mono"}
    assert r.value["clipping"]["clipped_samples"] == 0 and r.value["low_end_mono"]["mono_below_cutoff"] is True
    mono = rig.call("build_measure_report", path=wav("m", synth.drum_loop(140, bars=4, channels=1))).value
    assert "correlation" not in mono and "loudness" in mono


def test_failures(rig, tmp_path):
    assert rig.call("build_measure_report", path=str(tmp_path / "no.wav")).error.code == "E_IO"


def test_short_audio_skips_loudness_range_instead_of_failing(rig, wav):
    r = rig.call("build_measure_report", path=wav("short", synth.drum_loop(140, bars=1)))
    assert r.ok and "range" not in r.value and "3 second" in r.value["skipped"]["range"] and "loudness" in r.value
