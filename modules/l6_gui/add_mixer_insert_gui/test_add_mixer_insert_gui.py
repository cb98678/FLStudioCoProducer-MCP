import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "add_mixer_insert_gui.json").write_text(json.dumps(
        {"name": "add_mixer_insert_gui", "verified": True, "params": ['track_label', 'plugin'], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("add_mixer_insert_gui", track_label="abc", plugin="abc")
    assert r.ok and r.value == {"recipe": "add_mixer_insert_gui", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call('add_mixer_insert_gui', track_label='') .error.code == 'E_ARG'
    desk.halt.flag = True
    assert rig.call("add_mixer_insert_gui", track_label="abc", plugin="abc").error.code == "E_HALTED"
