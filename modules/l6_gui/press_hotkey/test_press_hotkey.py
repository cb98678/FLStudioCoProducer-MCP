def test_presses_chords(rig, desk):
    r = rig.call("press_hotkey", keys=["Ctrl", "Shift", "S"])
    assert r.value == {"pressed": ["ctrl", "shift", "s"]} and ("hotkey", ("ctrl", "shift", "s")) in desk.fake.log
    assert rig.call("press_hotkey", keys=["F8"]).ok


def test_refuses_unknown_and_dangerous_keys(rig, desk):
    for keys in (["alt", "f4"], ["ctrl", "alt", "delete"], ["win", "r"], ["f13"], ["ctrl", "ab"]):
        assert rig.call("press_hotkey", keys=keys).error.code == "E_ARG", keys
    assert not desk.fake.log
