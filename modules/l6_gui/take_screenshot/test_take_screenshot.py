def test_writes_a_png(rig, desk, tmp_path):
    (tmp_path / "s").mkdir()
    r = rig.call("take_screenshot", out_path=str(tmp_path / "s" / "a.png"))
    assert r.ok and r.value["width"] == 640 and (tmp_path / "s" / "a.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_outside_sandbox_and_not_ready(rig, desk, tmp_path):
    assert rig.call("take_screenshot", out_path="/etc/x.png").error.code == "E_SANDBOX_VIOLATION"
    desk.halt.flag = True
    assert rig.call("take_screenshot", out_path=str(tmp_path / "b.png")).error.code == "E_HALTED"


def test_creates_the_folder_it_writes_into(rig, desk, tmp_path):
    r = rig.call("take_screenshot", out_path=str(tmp_path / "new" / "deeper" / "a.png"))
    assert r.ok and (tmp_path / "new" / "deeper" / "a.png").is_file()
