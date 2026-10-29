import sys
from pathlib import Path

from coproducer import anatomy, flpfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_fxlib import mixer_project  # noqa: E402


def _src(tmp_path):
    src = tmp_path / "sandbox" / "in.flp"
    src.parent.mkdir(exist_ok=True)
    mixer_project({2: {0: "Fruity Parametric EQ 2"}}).save(str(src))
    return src


def test_builds_the_pump(rig, desk, tmp_path):
    from coproducer import automation

    src = _src(tmp_path)
    out = tmp_path / "sandbox" / "pumped.flp"
    r = rig.call("build_volume_pump", project=str(src), out_project=str(out), targets=[{"insert": 2, "depth": "deep"}, {"insert": 3, "depth_db": -30}])
    assert r.ok and r.meta["verified"] is True and r.value["kick"] == 0 and r.value["kick_notes"] == 1
    rep = anatomy.read(flpfile.Flp.load(str(out)))
    clips = {c["name"]: c for c in rep["automation"]["clips"]}
    assert clips["Pump 2"]["targets"] == [{"kind": "plugin", "insert": 2, "insert_name": "Insert 2", "slot": 9, "plugin": "Fruity Balance", "param": 1}]
    assert clips["Pump 3"]["targets"][0]["slot"] == 9 and clips["Pump 3"]["range"][0] < clips["Pump 2"]["range"][0] < 0.8
    pts = automation.list_automation(flpfile.Flp.load(str(out)))[0]["points"]
    assert [round(p[1], 3) for p in pts[:3]] == [round(automation.db_to_fader(-16.0), 3)] * 2 + [0.8] and [p[0] for p in pts[:3]] == [0.0, 0.1, 0.3]


def test_failures(rig, desk, tmp_path):
    src = _src(tmp_path)
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("build_volume_pump", project=str(src), out_project=out, targets=[]).error.code == "E_ARG"
    assert rig.call("build_volume_pump", project=str(src), out_project=out, targets=[{"insert": 2}], kick_channel=7).error.code == "E_ARG"
    assert rig.call("build_volume_pump", project=str(src), out_project="/elsewhere/x.flp", targets=[{"insert": 2}]).error.code == "E_SANDBOX_VIOLATION"
