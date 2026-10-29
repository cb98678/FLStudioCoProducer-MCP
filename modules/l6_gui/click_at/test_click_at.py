def test_clicks_inside_the_window(rig, desk):
    desk.fake.main["rect"] = (50, 20, 690, 380)
    r = rig.call("click_at", x=10, y=5, button="right", clicks=2)
    assert r.ok and r.value["screen"] == [60, 25] and ("click", 60, 25, "right", 2) in desk.fake.log


def test_refuses_outside_and_when_halted(rig, desk):
    assert rig.call("click_at", x=640, y=0).error.code == "E_ARG" and not [e for e in desk.fake.log if e[0] == "click"]
    desk.halt.flag = True
    assert rig.call("click_at", x=1, y=1).error.code == "E_HALTED"
