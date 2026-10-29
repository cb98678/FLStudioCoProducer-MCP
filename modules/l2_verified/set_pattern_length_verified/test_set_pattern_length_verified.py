def test_sets_length(rig):
    r = rig.call("set_pattern_length_verified", index=1, length=8)
    assert r.ok and r.meta["verified"] is True and rig.fake.patterns[1]["length"] == 8


def test_failures(rig):
    assert rig.call("set_pattern_length_verified", index=0, length=8).error.code == "E_ARG"
    assert rig.call("set_pattern_length_verified", index=999, length=8).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("set_pattern_length_verified", index=1, length=7).error.code == "E_NOT_VERIFIED"
