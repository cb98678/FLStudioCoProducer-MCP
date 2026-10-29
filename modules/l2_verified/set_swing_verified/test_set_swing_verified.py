def test_sets_swing(rig):
    r = rig.call("set_swing_verified", swing=0.3)
    assert r.ok and r.meta["verified"] is True and abs(rig.fake.swing - 0.3) < 1e-9
    assert rig.fake.calls("channels", "setSwing")


def test_failures(rig):
    assert rig.call("set_swing_verified", swing=2).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("set_swing_verified", swing=0.3).error.code == "E_NOT_VERIFIED"
