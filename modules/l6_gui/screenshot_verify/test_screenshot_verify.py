def test_passes_and_fails(rig, desk):
    ok = rig.call("screenshot_verify", expect={"title_contains": "fl studio", "no_dialog": True})
    assert ok.ok and ok.value["checks"] == {"title_contains": True, "no_dialog": True}
    desk.fake.open_dialog("Save as")
    r = rig.call("screenshot_verify", expect={"dialog_contains": "save", "no_dialog": True})
    assert r.error.code == "E_GUI_MISMATCH" and r.error.detail["checks"] == {"dialog_contains": True, "no_dialog": False}


def test_empty_expectation_and_halt(rig, desk):
    assert rig.call("screenshot_verify", expect={}).error.code == "E_GUI_MISMATCH"
    desk.halt.flag = True
    assert rig.call("screenshot_verify", expect={"no_dialog": True}).error.code == "E_HALTED"
