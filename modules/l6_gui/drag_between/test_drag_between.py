def test_drags(rig, desk):
    assert rig.call("drag_between", x1=1, y1=2, x2=30, y2=40).ok and ("drag", 1, 2, 30, 40) in desk.fake.log


def test_refuses_points_outside(rig, desk):
    assert rig.call("drag_between", x1=1, y1=2, x2=3000, y2=4).error.code == "E_ARG"
    assert not desk.fake.log
