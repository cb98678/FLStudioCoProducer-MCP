import sys
from pathlib import Path

from coproducer import anatomy, flpfile, sectiongain

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_fxlib import mixer_project  # noqa: E402


def _src(tmp_path):
    f = mixer_project({})
    f.add_playlist_clips([(1, 0, 16, 1)])  # the song runs 16 bars
    for bar, name in ((1, "Intro"), (5, "Build"), (9, "Drop")):
        f.add_time_marker((bar - 1) * 384, name)
    p = tmp_path / "sandbox" / "in.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_shapes_two_inserts_by_marker(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "g.flp"
    gains = [{"insert": 2, "sections": {"Build": -6}, "label": "Sub"}, {"insert": 3, "sections": {"Intro": -3, "Build": -3}},
             {"insert": 0, "sections": {"Build": -4}, "label": "Master"}]
    r = rig.call("apply_section_gains", project=str(_src(tmp_path)), out_project=str(out), gains=gains)
    assert r.ok and r.meta["verified"] is True
    assert [s["name"] for s in r.value["sections"]] == ["Intro", "Build", "Drop"] and r.value["sections"][-1]["end_bar"] == 17
    sub, other, master = r.value["placed"]
    assert master["slot"] == 0  # the master's first free slot, before any limiter
    assert (sub["insert"], sub["slot"], sub["length_beats"]) == (2, 9, 64.0)
    rep = anatomy.read(flpfile.Flp.load(str(out)))
    clips = {c["name"]: c for c in rep["automation"]["clips"]}
    t = clips["Section Gain Sub"]["targets"][0]
    assert (t["plugin"], t["insert"], t["slot"], t["param"]) == ("Fruity Balance", 2, 9, 1)
    assert clips["Section Gain Insert 3"]["range"][1] == 0.8  # back to 0 dB on the drop


def test_points_hold_each_section_and_ramp_into_changes():
    secs = [{"name": "A", "start_bar": 1, "end_bar": 5}, {"name": "B", "start_bar": 5, "end_bar": 9}]
    pts = sectiongain.gain_points(secs, {"B": -6}, 32.0)
    assert pts[0] == (0.0, 0.8) and (15.75, 0.8) in pts and pts[-1][0] == 32.0
    low = [v for b, v in pts if b >= 16]
    assert len(set(low)) == 1 and low[0] < 0.8


def test_failures(rig, desk, tmp_path):
    src = str(_src(tmp_path))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("apply_section_gains", project=src, out_project=out, gains=[]).error.code == "E_ARG"
    assert rig.call("apply_section_gains", project=src, out_project=out, gains=[{"insert": 1, "sections": {"Chorus": -3}}]).error.code == "E_ARG"
    assert rig.call("apply_section_gains", project=src, out_project="/elsewhere/x.flp", gains=[{"insert": 1, "sections": {"Drop": 1}}]).error.code == "E_SANDBOX_VIOLATION"


def test_default_map_by_role(rig, desk, tmp_path):
    from coproducer import testflp
    f = testflp.with_mixer(testflp.project({0: "Kick", 1: "Sub Bass", 2: "Vocal"}, {0: [0], 1: [96], 2: [0]}, bars=16), tracks=4)
    for ch, t in ((0, 1), (1, 2), (2, 3)):
        f.set_track(ch, t)
    p = tmp_path / "sandbox" / "roles.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    secs = [{"name": "Break 1", "start_bar": 1, "end_bar": 5}, {"name": "Buildup", "start_bar": 5, "end_bar": 9}, {"name": "Drop 1", "start_bar": 9, "end_bar": 17}]
    plan = sectiongain.gains_by_role(f, secs, sectiongain.DEFAULT_ROLE_GAINS)
    assert plan == [{"insert": 0, "sections": {"Buildup": -6.0}, "label": "Master"}, {"insert": 1, "sections": {"Buildup": -3.0}, "label": "Kick"},
                    {"insert": 2, "sections": {"Break 1": -7.8, "Buildup": -6.0}, "label": "Sub"}]  # the vocal has no entry: it stays as it is
    r = rig.call("apply_section_gains", project=str(p), out_project=str(tmp_path / "sandbox" / "r.flp"), by_role={}, sections=secs)
    assert not r.ok and r.error.code == "E_ARG"  # this synthetic project has no effect slots to put a Balance into


def test_scaled_map_and_contrast():
    assert sectiongain.scaled({"build": {"sub": -6.0}}, 0.5) == {"build": {"sub": -3.0}}
    rows = [{"section": "Break 1", "lufs": -10.4}, {"section": "Build 1", "lufs": -11.8}, {"section": "Drop 1", "lufs": -11.9}, {"section": "Outro", "lufs": -14.0}]
    assert sectiongain.contrast(rows) == [{"drop": "Drop 1", "before": "Build 1", "over_before_lu": -0.1, "over_loudest_break_lu": -1.5}]
