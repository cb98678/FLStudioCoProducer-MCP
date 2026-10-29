import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "export_split_stems_gui.json").write_text(json.dumps(
        {"name": "export_split_stems_gui", "verified": True, "params": ['path'], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("export_split_stems_gui", path=str(tmp_path / "x.bin"))
    assert r.ok and r.value == {"recipe": "export_split_stems_gui", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call('export_split_stems_gui', path='/elsewhere/x.bin').error.code == 'E_SANDBOX_VIOLATION'
    desk.halt.flag = True
    assert rig.call("export_split_stems_gui", path=str(tmp_path / "x.bin")).error.code == "E_HALTED"
