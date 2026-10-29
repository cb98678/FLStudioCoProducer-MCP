from coproducer.testflp import project


def test_reports_changes(rig, tmp_path):
    a = project({0: "Kick", 1: "Stab"}, {1: [0, 96, 192]}, bpm=120, presets={1: "CP - House Stab"})
    b = project({0: "Kick", 1: "Stab", 2: "Hat"}, {1: [0, 144, 192]}, bpm=124, presets={1: "Cowbell"})
    pa, pb = str(tmp_path / "a.flp"), str(tmp_path / "b.flp")
    a.save(pa)
    b.save(pb)
    r = rig.call("diff_flp_projects", before=pa, after=pb).value
    text = " | ".join(r["summary"])
    assert "channel added: Hat" in text and "preset 'CP - House Stab' to 'Cowbell'" in text and "tempo 120.0 to 124.0" in text
    stab = [n for n in r["report"]["notes"] if n["channel"] == "Stab"][0]
    assert stab["before"]["steps"] != stab["after"]["steps"]
    same = rig.call("diff_flp_projects", before=pa, after=pa).value
    assert same["changes"] == 0


def test_failures(rig, tmp_path):
    assert rig.call("diff_flp_projects", before=str(tmp_path / "no.flp"), after=str(tmp_path / "no2.flp")).error.code == "E_IO"
    assert rig.call("diff_flp_projects", before="", after="x").error.code == "E_ARG"
