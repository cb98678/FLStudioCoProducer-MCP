def test_lists_dialogs(rig, desk):
    assert rig.call("list_open_dialogs").value == {"dialogs": [], "count": 0}
    desk.fake.open_dialog("Save as")
    r = rig.call("list_open_dialogs")
    assert r.value["count"] == 1 and r.value["dialogs"][0]["title"] == "Save as"


def test_no_fl_window(rig, desk):
    desk.fake.find_window = lambda: None
    assert rig.call("list_open_dialogs").error.code == "E_NOT_FOUND"
