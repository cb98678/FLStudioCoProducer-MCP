from coproducer import flpfile, remixplan, songplan
from coproducer.testflp import remix_inputs

PLAN = "plans/friends_in_low_places.json"


def _inputs(tmp_path):
    songplan.apply(songplan.load(PLAN))
    (tmp_path / "sandbox").mkdir()
    return remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)


def test_builds_and_reads_back(rig, desk, tmp_path):
    i = _inputs(tmp_path)
    out = str(tmp_path / "sandbox" / "built.flp")
    r = rig.call("build_remix_project", base_project=i["base"], sytrus_project=i["sytrus"], audio_dir=i["audio"], out_project=out, plan_file=PLAN)
    assert r.ok and r.meta["verified"] and r.value["tempo"] == 124.0
    f = flpfile.Flp.load(out)
    assert "Chord Stab" in [f.channel_info(c)["name"] for c in f.channel_ids()]
    assert r.value["pattern_counts"]["Drums"] > 0 and len(r.value["vocal_clips"]) == 3
    solo = rig.call("build_remix_project", base_project=i["base"], sytrus_project=i["sytrus"], audio_dir=i["audio"],
                    out_project=str(tmp_path / "sandbox" / "solo.flp"), options={"solo": "kick"})
    g = flpfile.Flp.load(str(tmp_path / "sandbox" / "solo.flp"))
    assert solo.ok and [g.channel_info(c)["name"] for c in g.channel_ids() if g.channel_info(c)["enabled"]] == ["Kick"]


def test_failures(rig, desk, tmp_path):
    i = _inputs(tmp_path)
    args = dict(base_project=i["base"], sytrus_project=i["sytrus"], audio_dir=i["audio"])
    assert rig.call("build_remix_project", out_project=str(tmp_path.parent / "elsewhere.flp"), **args).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("build_remix_project", out_project=str(tmp_path / "sandbox" / "x.flp"), options={"kit": {"nope": "x.wav"}}, **args).error.code == "E_ARG"
    assert rig.call("build_remix_project", out_project=str(tmp_path / "sandbox" / "x.flp"), plan_file=str(tmp_path / "missing.json"), **args).error.code in ("E_IO", "E_NOT_FOUND")
    assert rig.call("build_remix_project", out_project=str(tmp_path / "sandbox" / "x.flp"), options={"colour": 1}, **args).error.code == "E_ARG"
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    assert rig.call("build_remix_project", out_project=str(tmp_path / "sandbox" / "x.flp"), plan_file=str(bad), **args).error.code == "E_ARG"
