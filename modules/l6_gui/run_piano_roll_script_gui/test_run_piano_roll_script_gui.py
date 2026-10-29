import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "run_piano_roll_script_gui.json").write_text(json.dumps(
        {"name": "run_piano_roll_script_gui", "verified": True, "params": [], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("run_piano_roll_script_gui", )
    assert r.ok and r.value == {"recipe": "run_piano_roll_script_gui", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    pass #
    desk.halt.flag = True
    assert rig.call("run_piano_roll_script_gui", ).error.code == "E_HALTED"
