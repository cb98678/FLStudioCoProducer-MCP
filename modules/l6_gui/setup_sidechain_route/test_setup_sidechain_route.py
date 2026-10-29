import json

from coproducer.services import set_service


def _stub(tmp_path, desk):
    desk.cfg["anchors"] = {"mixer_strip1_name": [10, 20], "mixer_send1_switch": [10, 90]}
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "set_sidechain_send_gui.json").write_text(json.dumps(
        {"name": "set_sidechain_send_gui", "verified": True, "params": ["source", "dest"], "steps": [
            {"do": "click_col", "anchor": "mixer_strip1_name", "param": "source", "dx": 42}]}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_routes_then_flags_the_send(rig, desk, tmp_path):
    _stub(tmp_path, desk)
    r = rig.call("setup_sidechain_route", source=1, dest=2)
    assert r.ok and r.value["route"]["bus"] == 2 and ("click", 10, 20, "left", 1) in desk.fake.log


def test_stops_when_the_route_fails(rig, desk, tmp_path):
    _stub(tmp_path, desk)
    r = rig.call("setup_sidechain_route", source=1, dest=99)
    assert not r.ok and not any(e[0] == "click" for e in desk.fake.log)
