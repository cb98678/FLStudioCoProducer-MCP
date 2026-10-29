import json

from coproducer.services import set_service


def _stub(tmp_path):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "set_limiter_sidechain_gui.json").write_text(json.dumps(
        {"name": "set_limiter_sidechain_gui", "verified": True, "params": ["dest", "position"], "steps": [
            {"do": "click_in_window", "title": "(Insert {dest})", "dx": 5, "dy": 10, "param": "position", "dy_each": 19}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_clicks_the_listed_source(rig, desk, tmp_path):
    _stub(tmp_path)
    desk.fake.open_dialog("Fruity Limiter (Insert 2)")
    assert rig.call("set_sidechain_source_gui", dest=2, position=2).ok
    assert ("click", 105, 129, "left", 1) in desk.fake.log


def test_refuses_missing_window(rig, desk, tmp_path):
    _stub(tmp_path)
    assert rig.call("set_sidechain_source_gui", dest=3).error.code == "E_GUI_MISMATCH"
