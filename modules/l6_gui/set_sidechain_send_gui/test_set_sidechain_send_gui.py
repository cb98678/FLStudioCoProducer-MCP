import json

from coproducer.services import set_service


def _stub(tmp_path, desk):
    desk.cfg["anchors"] = {"mixer_strip1_name": [10, 20], "mixer_send1_switch": [10, 90]}
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "set_sidechain_send_gui.json").write_text(json.dumps(
        {"name": "set_sidechain_send_gui", "verified": True, "params": ["source", "dest"], "steps": [
            {"do": "click_col", "anchor": "mixer_strip1_name", "param": "source", "dx": 42},
            {"do": "click_col", "anchor": "mixer_send1_switch", "param": "dest", "dx": 42, "button": "right"}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_clicks_source_then_destination(rig, desk, tmp_path):
    _stub(tmp_path, desk)
    r = rig.call("set_sidechain_send_gui", source=1, dest=2)
    assert r.ok and ("click", 10, 20, "left", 1) in desk.fake.log and ("click", 52, 90, "right", 1) in desk.fake.log


def test_refuses_same_track(rig, desk, tmp_path):
    _stub(tmp_path, desk)
    assert rig.call("set_sidechain_send_gui", source=2, dest=2).error.code == "E_ARG"
