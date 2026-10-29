def test_adds_and_finds_marker(rig):
    rig.call("add_time_marker_verified", time=0, name="Intro")
    r = rig.call("add_time_marker_verified", time=1536, name="Drop")
    assert r.ok and r.value == 1 and r.meta["verified"] is True and rig.fake.markers[1] == (1536, "Drop")


def test_failures(rig):
    assert rig.call("add_time_marker_verified", time=-1, name="x").error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("add_time_marker_verified", time=0, name="Drop").error.code == "E_NOT_VERIFIED"
