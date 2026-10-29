import json

from coproducer.services import set_service


def _allow(tmp_path, allow):
    (tmp_path / "recipes").mkdir(exist_ok=True)
    (tmp_path / "recipes" / "_dialogs.json").write_text(json.dumps({"allow": allow}))
    set_service("recipes_dir", str(tmp_path / "recipes"))


def test_closes_allowed_dialog(rig, desk, tmp_path):
    rig.reg.approver = lambda name, kwargs: True
    assert rig.call("dismiss_dialog_gui").value == {"dismissed": False}
    _allow(tmp_path, [{"contains": "tip of the day", "key": "esc"}])
    desk.fake.open_dialog("Tip of the Day")
    r = rig.call("dismiss_dialog_gui")
    assert r.ok and r.value["dismissed"] and r.value["key"] == "esc"


def test_unknown_dialog_halts(rig, desk, tmp_path):
    rig.reg.approver = lambda name, kwargs: True
    _allow(tmp_path, [])
    desk.fake.open_dialog("Unsaved changes")
    r = rig.call("dismiss_dialog_gui")
    assert r.error.code == "E_BLOCKED_BY_DIALOG" and desk.halt.flag is True and r.error.detail["title"] == "Unsaved changes"
