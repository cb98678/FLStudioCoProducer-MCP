import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "load_plugin_gui.json").write_text(json.dumps(
        {"name": "load_plugin_gui", "verified": True, "params": ['name'], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("load_plugin_gui", name="abc")
    assert r.ok and r.value == {"recipe": "load_plugin_gui", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call('load_plugin_gui', name='') .error.code == 'E_ARG'
    desk.halt.flag = True
    assert rig.call("load_plugin_gui", name="abc").error.code == "E_HALTED"
