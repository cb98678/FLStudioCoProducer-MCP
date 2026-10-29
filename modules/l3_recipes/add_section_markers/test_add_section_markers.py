from coproducer import flpfile, testflp


def _src(tmp_path):
    p = tmp_path / "sandbox" / "in.flp"
    p.parent.mkdir(exist_ok=True)
    testflp.project({0: "Kick"}, {0: [0]}, bars=8).save(str(p))
    return p


def test_writes_markers(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "m.flp"
    r = rig.call("add_section_markers", project=str(_src(tmp_path)), out_project=str(out), sections=[{"name": "Drop", "bar": 5}, {"name": "Intro", "bar": 1}])
    assert r.ok and r.meta["verified"] is True and r.value["markers"] == ["Intro", "Drop"]
    assert flpfile.Flp.load(str(out)).time_markers()[1]["pos"] == 4 * 384


def test_failures(rig, desk, tmp_path):
    src = str(_src(tmp_path))
    assert rig.call("add_section_markers", project=src, out_project=str(tmp_path / "sandbox" / "x.flp"), sections=[]).error.code == "E_ARG"
    assert rig.call("add_section_markers", project=src, out_project="/elsewhere/x.flp", sections=[{"name": "A", "bar": 1}]).error.code == "E_SANDBOX_VIOLATION"
