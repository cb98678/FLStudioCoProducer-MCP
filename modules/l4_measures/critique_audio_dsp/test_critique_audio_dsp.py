import numpy as np

from coproducer import synth


def areas(r):
    return {(o["area"], o["severity"]) for o in r.value["observations"]}


def test_flags_problems(rig, wav):
    hot = np.clip(synth.drum_loop(140, bars=2) * 4.0, -1, 1)           # slammed into the ceiling
    r = rig.call("critique_audio_dsp", path=wav("hot", hot))
    assert r.ok and r.value["source"] == "dsp"
    assert ("clipping", "high") in areas(r) and ("peaks", "high") in areas(r)
    assert r.value["observations"][0]["severity"] == "high"
    out_of_phase = np.column_stack([hot[:, 0], -hot[:, 0]]) * 0.2
    assert ("stereo", "high") in areas(rig.call("critique_audio_dsp", path=wav("phase", out_of_phase)))
    quiet = rig.call("critique_audio_dsp", path=wav("quiet", synth.drum_loop(140, bars=2) * 0.05))
    assert ("loudness", "medium") in areas(quiet)


def test_clean_and_missing_files(rig, wav, tmp_path):
    mix = synth.drum_loop(140, bars=2) * 0.2
    r = rig.call("critique_audio_dsp", path=wav("ok", mix), loudness_target_lufs=-23.0)
    assert not [o for o in r.value["observations"] if o["severity"] == "high"]
    assert rig.call("critique_audio_dsp", path=str(tmp_path / "no.wav")).error.code == "E_IO"
