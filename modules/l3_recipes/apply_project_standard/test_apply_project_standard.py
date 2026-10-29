from coproducer import flporg, flpfile, projorg
from coproducer.testflp import project, with_organization


def _src(tmp_path):
    f = with_organization(project({0: "Kick", 1: "909 CH 2", 2: "707 OH", 3: "Chord Stab", 4: "CP_Chop_hook", 5: "FX bed", 6: "Mystery", 7: "Leftover"}, {0: [0]}))
    for c in range(7):
        f.set_track(c, c + 1)
    f.set_track(7, 0)  # routed to no insert
    f.add_pattern(2, "Drums 1", b"")
    src = tmp_path / "mix.flp"
    f.save(str(src))
    return src


def test_organizes(rig, desk, tmp_path):
    src = _src(tmp_path)
    before = src.read_bytes()
    out = tmp_path / "sandbox" / "org.flp"
    out.parent.mkdir()
    r = rig.call("apply_project_standard", project=str(src), out_project=str(out))
    assert r.ok and r.meta["verified"] and r.value["left"] == []
    assert r.value["unclassified_channels"] == ["Mystery", "Leftover"]
    g = flpfile.Flp.load(str(out))
    names = {c: g.channel_info(c)["name"] for c in g.channel_ids()}
    assert names[1] == "Hat Closed" and names[2] == "Hat Open" and names[4] == "Chop Hook"
    assert flporg.channel_color(g, 0) == projorg.PALETTE["drums"] and flporg.channel_color(g, 4) == projorg.PALETTE["vocals"]
    assert flporg.channel_color(g, 6) == (92, 101, 106)  # unknown family left alone
    groups = flporg.display_groups(g)
    assert groups[flporg.channel_group(g, 0)] == "Drums" and groups[flporg.channel_group(g, 3)] == "Synths" and groups[flporg.channel_group(g, 5)] == "FX"
    assert flporg.insert_name(g, 2) == "Hat Closed" and flporg.insert_color(g, 4) == projorg.PALETTE["synths"]
    assert flporg.pattern_name(g, 2) == "Drums 1"
    assert src.read_bytes() == before
    again = rig.call("apply_project_standard", project=str(out), out_project=str(tmp_path / "sandbox" / "org2.flp"))
    assert again.value["left"] == [] and (tmp_path / "sandbox" / "org2.flp").read_bytes() == out.read_bytes()  # idempotent


def test_unused_channels_are_listed_and_dropped_on_request(rig, desk, tmp_path):
    src = _src(tmp_path)
    out = tmp_path / "sandbox" / "keep.flp"
    out.parent.mkdir(exist_ok=True)
    kept = rig.call("apply_project_standard", project=str(src), out_project=str(out))
    assert kept.ok and "Mystery" in kept.value["unused_channels"] and kept.value["dropped"] == []
    assert len(flpfile.Flp.load(str(out)).channel_ids()) == 8
    out2 = tmp_path / "sandbox" / "drop.flp"
    dropped = rig.call("apply_project_standard", project=str(src), out_project=str(out2), drop_unused=True)
    g = flpfile.Flp.load(str(out2))
    assert dropped.ok and dropped.value["dropped"] == ["Leftover"] and dropped.value["left"] == []
    names = [g.channel_info(c)["name"] for c in g.channel_ids()]
    assert "Leftover" not in names and "Mystery" in names  # the stray goes, the silent one on an insert stays
    assert g.channel_ids() == list(range(len(g.channel_ids())))  # contiguous ids
    assert flporg.display_groups(g)  # still organized


def test_dry_run_writes_nothing(rig, desk, tmp_path):
    src = _src(tmp_path)
    out = tmp_path / "sandbox" / "org.flp"
    r = rig.call("apply_project_standard", project=str(src), out_project=str(out), dry_run=True)
    assert r.ok and r.value["problems"] and not out.exists()


def test_failures(rig, desk, tmp_path):
    assert rig.call("apply_project_standard", project=str(tmp_path / "mix.flp"), out_project="/elsewhere/x.flp").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("apply_project_standard", project=str(tmp_path / "no.flp"), out_project=str(tmp_path / "sandbox" / "x.flp")).error.code == "E_IO"
    assert rig.call("apply_project_standard", project="", out_project="x").error.code == "E_ARG"
