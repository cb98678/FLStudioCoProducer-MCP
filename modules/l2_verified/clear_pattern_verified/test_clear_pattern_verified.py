def test_clears_a_pattern_with_data(rig):
    rig.fake.patterns[2]["notes"] = [1, 2, 3]
    r = rig.call("clear_pattern_verified", index=2)
    assert r.ok and r.meta["verified"] is True and r.value == {"cleared": True, "was_empty": False}
    assert rig.fake.patterns[2]["notes"] == [] and rig.fake.calls("patterns", "clearPattern")


def test_empty_pattern_is_left_alone(rig):
    r = rig.call("clear_pattern_verified", index=1)
    assert r.ok and r.value == {"cleared": False, "was_empty": True} and not rig.fake.calls("patterns", "clearPattern")


def test_failures(rig):
    assert rig.call("clear_pattern_verified", index=0).error.code == "E_ARG"
    assert rig.call("clear_pattern_verified", index=999).error.code == "E_ARG"
    rig.fake.patterns[2]["notes"] = [1]
    rig.fake.ignore_writes = True
    assert rig.call("clear_pattern_verified", index=2).error.code == "E_NOT_VERIFIED"
