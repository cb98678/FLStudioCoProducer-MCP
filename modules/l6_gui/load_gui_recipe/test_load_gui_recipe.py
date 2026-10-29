import json

from coproducer.services import set_service

SHIPPED = ["add_mixer_insert_gui", "arm_piano_roll_script_gui", "export_split_stems_gui", "import_midi_gui", "load_plugin_gui",
           "load_sample_gui", "open_plugin_ui_gui", "open_project_copy", "run_piano_roll_script_gui", "save_project_copy"]
VERIFIED = {"arm_piano_roll_script_gui", "run_piano_roll_script_gui", "load_plugin_gui"}   # calibrated on the real FL (load_plugin_gui on 2026-10-22)


def test_loads_every_shipped_recipe(rig, desk):
    for name in SHIPPED:
        r = rig.call("load_gui_recipe", name=name)
        assert r.ok and r.value["name"] == name and r.value["verified"] is (name in VERIFIED), name
        assert "—" not in json.dumps(r.value)


def test_unknown_and_broken_recipes(rig, desk, tmp_path):
    assert rig.call("load_gui_recipe", name="nope").error.code == "E_NOT_FOUND"
    assert rig.call("load_gui_recipe", name="../etc").error.code == "E_ARG"
    set_service("recipes_dir", str(tmp_path))
    (tmp_path / "bad.json").write_text("{not json")
    (tmp_path / "odd.json").write_text(json.dumps({"params": [], "steps": [{"do": "teleport"}]}))
    assert rig.call("load_gui_recipe", name="bad").error.code == "E_IO"
    assert rig.call("load_gui_recipe", name="odd").error.code == "E_ARG"
