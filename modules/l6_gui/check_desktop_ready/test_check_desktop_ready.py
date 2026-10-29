from coproducer.services import clear_services


def test_ready_and_window_info(rig, desk):
    r = rig.call("check_desktop_ready")
    assert r.ok and r.value["width"] == 640 and r.value["height"] == 360 and r.value["title"] == "FL Studio 2026"
    desk.fake.fg_pid = 99                                   # another program has focus; FL takes it back
    assert rig.call("check_desktop_ready").ok and desk.fake.fg_pid == 7 and ("focus", 100) in desk.fake.log


def test_every_refusal(rig, desk):
    desk.halt.flag = True
    assert rig.call("check_desktop_ready").error.code == "E_HALTED"
    desk.halt.flag = False
    desk.fake.fg_pid, desk.fake.refuse_focus = 99, True
    assert rig.call("check_desktop_ready").error.code == "E_GUI_MISMATCH"
    desk.fake.fg_pid, desk.fake.refuse_focus = 7, False
    desk.cfg["display_scale"] = 1.5
    r = rig.call("check_desktop_ready")
    assert r.error.code == "E_GUI_MISMATCH" and "1.00" in r.error.message
    desk.cfg["display_scale"] = 0.0
    desk.fake.find_window = lambda: None
    assert rig.call("check_desktop_ready").error.code == "E_NOT_FOUND"
    clear_services()
    assert rig.call("check_desktop_ready").error.code == "E_UNSUPPORTED_API"


def test_a_locked_screen_is_named(rig, desk):
    desk.fake.fg_pid = 0
    r = rig.call("check_desktop_ready")
    assert r.error.code == "E_GUI_MISMATCH" and "locked" in r.error.message and ("focus", 100) not in desk.fake.log
