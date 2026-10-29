import sys
from pathlib import Path

from coproducer import fxlib

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_fxlib import mixer_project  # noqa: E402


def test_places_an_entry(rig, desk, tmp_path):
    src = tmp_path / "sandbox" / "in.flp"
    src.parent.mkdir()
    mixer_project({}).save(str(src))
    name = fxlib.list_entries()[0]["name"]
    out = tmp_path / "sandbox" / "out.flp"
    r = rig.call("apply_effect_from_library", project=str(src), out_project=str(out), placements=[{"insert": 2, "slot": 0, "name": name}])
    assert r.ok and r.meta["verified"] is True and r.value["placed"][0]["plugin"] == fxlib.load_entry(name)["plugin"]


def test_failures(rig, desk, tmp_path):
    src = tmp_path / "sandbox" / "in.flp"
    src.parent.mkdir()
    mixer_project({2: {0: "Fruity Balance"}}).save(str(src))
    name = fxlib.list_entries()[0]["name"]
    out = str(tmp_path / "sandbox" / "out.flp")
    assert rig.call("apply_effect_from_library", project=str(src), out_project=out, placements=[{"insert": 2, "slot": 0, "name": name}]).error.code == "E_ARG"
    assert rig.call("apply_effect_from_library", project=str(src), out_project=out, placements=[{"insert": 1, "slot": 0, "name": "no such"}]).error.code == "E_ARG"
    assert rig.call("apply_effect_from_library", project=str(src), out_project=out, placements=[]).error.code == "E_ARG"
    assert rig.call("apply_effect_from_library", project=str(src), out_project="/elsewhere/x.flp", placements=[{"insert": 1, "slot": 0, "name": name}]).error.code == "E_SANDBOX_VIOLATION"
