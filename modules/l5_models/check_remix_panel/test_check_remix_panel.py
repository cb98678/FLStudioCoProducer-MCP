import json

import numpy as np
import soundfile as sf

from coproducer import songplan
from coproducer.services import set_service
from coproducer.synth import drum_loop


def _files(tmp_path, gain=0.4):
    plan = songplan.load("plans/friends_in_low_places.json")
    plan.update(style="dubstep", bpm=140.0)
    pf = tmp_path / "plan.json"
    pf.write_text(json.dumps(plan))
    x = np.asarray(drum_loop(140, bars=44), dtype=float)  # past the first drop (bar 24 of the plan) and its 16 s excerpt
    sf.write(str(tmp_path / "m.wav"), (x / np.abs(x).max() * gain).astype("float32"), 44100)
    return str(tmp_path / "m.wav"), str(pf)


def test_panel_passes_a_good_master_and_grades_the_critic(rig, ml, tmp_path, monkeypatch):
    set_service("sandbox_root", str(tmp_path))
    rig.reg.approver = lambda n, kw: n == "check_remix_panel"
    wav, plan = _files(tmp_path)
    monkeypatch.setenv("FAKE_CRITIQUE_REPLY", "No.")
    r = rig.call("check_remix_panel", path=wav, plan_file=plan, targets_file="targets/club_release.toml")
    assert r.ok and r.value["critic"]["asked"] >= 2
    assert r.value["critic"]["grade"] is not None
    assert any(p["item"].startswith("loudness") for p in r.value["problems"])     # a -20 LUFS file fails the club loudness: dsp is trusted
    assert any(p["item"] == "length against the plan" for p in r.value["problems"])  # 44 bars rendered for a whole song's plan


def test_problems_stand_and_a_failed_critic_is_not_trusted(rig, ml, tmp_path, monkeypatch):
    set_service("sandbox_root", str(tmp_path))
    rig.reg.approver = lambda n, kw: n == "check_remix_panel"
    wav, plan = _files(tmp_path)
    monkeypatch.setenv("FAKE_CRITIQUE_REPLY", "Yes, absolutely.")
    r = rig.call("check_remix_panel", path=wav, plan_file=plan, targets_file="targets/club_release.toml")
    assert r.ok and r.value["critic"]["trusted"] is False                         # "yes" to four on the floor in a half-time drop is wrong
    assert all(n["acted_on"] is False for n in r.value["notes"])
    assert rig.call("check_remix_panel", path=str(tmp_path / "x.wav"), plan_file=plan, targets_file="targets/club_release.toml").error.code == "E_NOT_FOUND"


def test_tonal_balance_judge_uses_the_reference_profile(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    rig.reg.approver = lambda n, kw: n == "check_remix_panel"
    wav, plan = _files(tmp_path)
    assert rig.call("build_reference_profile", paths=[wav], out_file=str(tmp_path / "prof.json")).ok
    r = rig.call("check_remix_panel", path=wav, plan_file=plan, targets_file="targets/club_release.toml", options={"critic": False, "profile": str(tmp_path / "prof.json")})
    row = next(f for f in r.value["findings"] if f["item"] == "tonal balance against the references")
    assert row["ok"] and row["detail"]["outside"] == 0                            # the track is its own reference


def test_separation_judge_sets_the_voice_truth(rig, ml, tmp_path, monkeypatch):
    set_service("sandbox_root", str(tmp_path))
    rig.reg.approver = lambda n, kw: n == "check_remix_panel"
    wav, plan = _files(tmp_path)
    monkeypatch.setenv("FAKE_CRITIQUE_REPLY", "No.")
    r = rig.call("check_remix_panel", path=wav, plan_file=plan, targets_file="targets/club_release.toml")
    sep = [f for f in r.value["findings"] if f["judge"] == "separation"]
    assert sep and sep[0]["item"] == "voice audible in the first drop" and "vocal_minus_mix_lu" in sep[0]["detail"]
    voice_row = r.value["critic"]["rows"][-1]                                     # asked "purely instrumental?": yes means no voice
    assert voice_row["expect"] == (sep[0]["detail"]["vocal_minus_mix_lu"] < -20.0)    # graded on what separation measured, not on the plan


def test_flat_drops_are_asked_about_not_failed():
    from modules.l5_models.check_remix_panel.check_remix_panel import _flat_drops
    rows = [{"drop": "Drop 1", "before": "Groove 1", "over_before_lu": 0.08}, {"drop": "Drop 2", "before": "Build", "over_before_lu": 0.2},
            {"drop": "Drop 3", "before": "Groove 2", "over_before_lu": 2.4}]
    got = _flat_drops(rows)
    assert len(got) == 1 and [d["drop"] for d in got[0]["detail"]] == ["Drop 1"]      # a build drop is the contrast judge's, not this one
    assert _flat_drops([{"drop": "Drop 1", "before": "Groove", "over_before_lu": 1.5}]) == []
