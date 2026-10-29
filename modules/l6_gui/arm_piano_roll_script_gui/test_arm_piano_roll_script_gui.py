import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "arm_piano_roll_script_gui.json").write_text(json.dumps(
        {"name": "arm_piano_roll_script_gui", "verified": True, "params": ['script'], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("arm_piano_roll_script_gui", script="abc")
    assert r.ok and r.value == {"recipe": "arm_piano_roll_script_gui", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call('arm_piano_roll_script_gui', script='') .error.code == 'E_ARG'
    desk.halt.flag = True
    assert rig.call("arm_piano_roll_script_gui", script="abc").error.code == "E_HALTED"
