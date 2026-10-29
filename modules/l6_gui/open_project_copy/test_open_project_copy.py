import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "open_project_copy.json").write_text(json.dumps(
        {"name": "open_project_copy", "verified": True, "params": ['path'], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("open_project_copy", path=str(tmp_path / "x.bin"))
    assert r.ok and r.value == {"recipe": "open_project_copy", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call('open_project_copy', path='/elsewhere/x.bin').error.code == 'E_SANDBOX_VIOLATION'
    desk.halt.flag = True
    assert rig.call("open_project_copy", path=str(tmp_path / "x.bin")).error.code == "E_HALTED"
