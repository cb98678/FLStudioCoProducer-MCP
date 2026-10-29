def test_sets_all_levels(rig):
    r = rig.call("set_rough_balance", levels_db={"1": -3.0, "2": -8.5, "3": 0.0})
    assert r.ok and r.meta["verified"] is True
    assert all(abs(r.value["achieved_db"][k] - want) <= 0.15 for k, want in {"1": -3.0, "2": -8.5, "3": 0.0}.items())


def test_failures(rig):
    assert rig.call("set_rough_balance", levels_db={"99": -3.0}).error.code == "E_ARG"
    assert rig.call("set_rough_balance", levels_db={"1": -90.0}).error.code == "E_ARG"
