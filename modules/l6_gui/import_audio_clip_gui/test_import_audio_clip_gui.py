import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "import_audio_clip_gui.json").write_text(json.dumps(
        {"name": "import_audio_clip_gui", "verified": True, "params": ["path"], "steps": [{"do": "hotkey", "keys": ["f9"]}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))
    set_service("sandbox_root", str(tmp_path))


def test_runs_its_recipe_with_the_resolved_path(rig, desk, tmp_path):
    _stub(tmp_path)
    (tmp_path / "a.wav").write_bytes(b"RIFF")
    r = rig.call("import_audio_clip_gui", path=str(tmp_path / "a.wav"))
    assert r.ok and r.value == {"recipe": "import_audio_clip_gui", "steps_run": 1}


def test_refuses_paths_outside_the_sandbox(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call("import_audio_clip_gui", path="/elsewhere/a.wav").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("import_audio_clip_gui", path="").error.code == "E_ARG"
    desk.halt.flag = True
    assert rig.call("import_audio_clip_gui", path=str(tmp_path / "a.wav")).error.code == "E_HALTED"
