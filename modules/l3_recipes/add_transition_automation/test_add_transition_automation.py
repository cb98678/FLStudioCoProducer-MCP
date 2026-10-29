import sys
from pathlib import Path

from coproducer import anatomy, flpfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_fxlib import mixer_project  # noqa: E402


def _src(tmp_path):
    f = mixer_project({})
    f.add_time_marker(8 * 384, "Drop")
    p = tmp_path / "sandbox" / "in.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_adds_each_recipe(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "t.flp"
    todo = [{"recipe": "filter_sweep", "at": "Drop", "insert": 2, "bars": 4}, {"recipe": "reverb_throw", "at": "drop", "insert": 2},
            {"recipe": "pitch_rise", "at": 9, "channel": 0}, {"recipe": "fade_in", "at": "Drop", "insert": 3}, {"recipe": "gap", "at": "Drop", "insert": 1, "beats": 1}]
    r = rig.call("add_transition_automation", project=str(_src(tmp_path)), out_project=str(out), transitions_list=todo)
    assert r.ok and r.meta["verified"] is True and [p["moment_beat"] for p in r.value["placed"]] == [32.0] * 5
    rep = anatomy.read(flpfile.Flp.load(str(out)))
    targets = {c["name"]: c["targets"][0] for c in rep["automation"]["clips"]}
    assert targets["Filter Sweep Drop"]["plugin"] == "Fruity Filter" and targets["Filter Sweep Drop"]["slot"] == 0
    assert targets["Reverb Throw drop"]["plugin"] == "Fruity Reeverb 2" and targets["Reverb Throw drop"]["param"] == 12
    assert targets["Pitch Rise 9"] == {"kind": "channel", "channel": 0, "channel_name": "Kick", "param": "pitch"}
    assert targets["Fade In Drop"]["plugin"] == "Fruity Balance" and targets["Gap Drop"]["insert"] == 1
    clips = {c["name"]: c for c in rep["automation"]["clips"]}
    assert clips["Pitch Rise 9"]["range"] == [0.5, 0.625]  # +12 semitones: a pitch clip spans -48..+48 (measured in FL's render)
    assert clips["Filter Sweep Drop"]["beats"] == 17.0 and clips["Filter Sweep Drop"]["range"] == [0.01, 0.42] and clips["Gap Drop"]["range"] == [0.0, 0.8]  # rests at 0.01: at 0 the high-pass held a DC offset


def test_failures(rig, desk, tmp_path):
    src = str(_src(tmp_path))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("add_transition_automation", project=src, out_project=out, transitions_list=[{"recipe": "gap", "at": "Chorus", "insert": 1}]).error.code == "E_ARG"
    assert rig.call("add_transition_automation", project=src, out_project=out, transitions_list=[{"recipe": "pitch_rise", "at": 9}]).error.code == "E_ARG"
    assert rig.call("add_transition_automation", project=src, out_project=out, transitions_list=[]).error.code == "E_ARG"


def test_new_recipes_get_their_own_named_plugins(rig, desk, tmp_path):
    from coproducer import fxlib
    out = tmp_path / "sandbox" / "n.flp"
    todo = [{"recipe": "lowpass_open", "at": "Drop", "insert": 1, "bars": 4}, {"recipe": "filter_wobble", "at": "Drop", "insert": 2, "bars": 2, "period": 0.5},
            {"recipe": "fx_swell", "at": "Drop", "insert": 3, "beats": 4}, {"recipe": "reverb_throw", "at": "Drop", "insert": 3}, {"recipe": "gap", "at": "Drop", "insert": 3, "beats": 1}]
    r = rig.call("add_transition_automation", project=str(_src(tmp_path)), out_project=str(out), transitions_list=todo)
    assert r.ok and r.meta["verified"] is True
    lp, wob, swell, throw, gap = r.value["placed"]
    assert wob["copies"] == 16 and "dry_clip" in swell and "dry_clip" in throw
    g = flpfile.Flp.load(str(out))
    names = {s: fxlib.slot_name(g, 3, s) for s in range(10) if fxlib.slot_plugin(g, 3, s)}
    assert sorted(names.values()) == ["Gap Gain", "Throw Reverb", "Transition Flanger"]
    assert fxlib.slot_plugin(g, 1, lp["slot"]) == "Fruity Love Philter" and fxlib.slot_name(g, 2, wob["slot"]) == "Wobble Lowpass"
    starts = sorted(it[0] for it in [(int.from_bytes(x[0:4], "little") / 96,) for x in g.playlist_items() if int.from_bytes(x[6:8], "little") == wob["clip"]])
    assert starts[:3] == [32.0, 32.5, 33.0] and len(starts) == 16
    rep = anatomy.read(g)
    clips = {c["name"]: c for c in rep["automation"]["clips"]}
    assert clips["Reverb Throw Dry Drop"]["targets"][0]["param"] == 10 and clips["Fx Swell Dry Drop"]["targets"][0]["param"] == 9


def test_gross_beat_fills_use_the_measured_slots(rig, desk, tmp_path):
    from coproducer import fxlib
    out = tmp_path / "sandbox" / "gb.flp"
    todo = [{"recipe": "stutter_fill", "at": "Drop", "insert": 1, "bars": 1}, {"recipe": "tape_stop", "at": 5, "insert": 1}]
    r = rig.call("add_transition_automation", project=str(_src(tmp_path)), out_project=str(out), transitions_list=todo)
    assert r.ok and r.value["placed"][0]["slot"] == r.value["placed"][1]["slot"]  # one Gross Beat per insert, shared by its fills
    g = flpfile.Flp.load(str(out))
    assert fxlib.slot_name(g, 1, r.value["placed"][0]["slot"]) == "Transition Gross Beat"
    clips = {c["name"]: c for c in anatomy.read(g)["automation"]["clips"]}
    assert clips["Stutter Fill Drop"]["range"] == [0.0, round(4 / 35, 4)] or abs(clips["Stutter Fill Drop"]["range"][1] - 4 / 35) < 1e-3
    bad = rig.call("add_transition_automation", project=str(_src(tmp_path)), out_project=str(out), transitions_list=[{"recipe": "reverse_fill", "at": "Drop", "insert": 1, "bars": 0.5}])
    assert bad.error.code == "E_ARG"
