import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "open_plugin_ui_gui.json").write_text(json.dumps(
        {"name": "open_plugin_ui_gui", "verified": True, "params": ['target'], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_runs_its_recipe(rig, desk, tmp_path):
    _stub(tmp_path)
    r = rig.call("open_plugin_ui_gui", target="abc")
    assert r.ok and r.value == {"recipe": "open_plugin_ui_gui", "steps_run": 1}


def test_refuses_bad_input(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call('open_plugin_ui_gui', target='') .error.code == 'E_ARG'
    desk.halt.flag = True
    assert rig.call("open_plugin_ui_gui", target="abc").error.code == "E_HALTED"
