import pytest

from coproducer import synth


@pytest.mark.parametrize("bpm", [128, 140, 174])
def test_finds_the_tempo(rig, wav, bpm):
    r = rig.call("estimate_bpm_dsp", path=wav("loop", synth.drum_loop(bpm, bars=8)))
    assert r.ok and any(abs(c["bpm"] - bpm) < 1.5 for c in r.value["candidates"][:3]), (bpm, r.value)


def test_failures(rig, wav, tmp_path):
    assert rig.call("estimate_bpm_dsp", path=str(tmp_path / "no.wav")).error.code == "E_IO"
    assert rig.call("estimate_bpm_dsp", path=wav("s", synth.sine(440, 0.05))).error.code == "E_ARG"


def test_hint_picks_the_candidate_near_the_expected_tempo_and_flags_ambiguity(rig, wav, monkeypatch):
    from coproducer import dsp
    monkeypatch.setattr(dsp, "estimate_tempo", lambda x, r, lo, hi: [{"bpm": 85.29, "strength": 0.505}, {"bpm": 127.89, "strength": 0.495}, {"bpm": 63.97, "strength": 0.469}])
    path = wav("loop", synth.drum_loop(128, bars=8))
    plain = rig.call("estimate_bpm_dsp", path=path)
    assert plain.value["bpm"] == 85.29 and plain.value["ambiguous"] is True and "matched_hint" not in plain.value
    hinted = rig.call("estimate_bpm_dsp", path=path, hint_bpm=128.0)
    assert hinted.value["bpm"] == 127.89 and hinted.value["matched_hint"] is True
    miss = rig.call("estimate_bpm_dsp", path=path, hint_bpm=170.0)
    assert miss.value["bpm"] == 85.29 and miss.value["matched_hint"] is False
