from pathlib import Path


def test_locates_an_element(rig, desk, ml, tmp_path):
    (tmp_path / "screens").mkdir()
    r = rig.call("locate_element", description="the play button")
    assert r.ok and (r.value["x"], r.value["y"]) == (10, 20) and Path(tmp_path / "screens" / "_locate.png").is_file()


def test_failures_pass_through(rig, desk, ml, tmp_path, monkeypatch):
    (tmp_path / "screens").mkdir()
    assert rig.call("locate_element", description="the play button", min_confidence=0.95).error.code == "E_GUI_MISMATCH"
    desk.halt.flag = True
    assert rig.call("locate_element", description="the play button").error.code == "E_HALTED"
