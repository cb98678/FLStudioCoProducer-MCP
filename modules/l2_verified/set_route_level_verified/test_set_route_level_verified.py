"""Tests for set_route_level_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_route_level_verified", index=1, dest_index=0, level=0.4)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.mixer[1]['routes'][0] - 0.4) < 1e-9
    assert rig.fake.calls("mixer", "setRouteToLevel")


def test_failures(rig):
    assert rig.call("set_route_level_verified", index=1, dest_index=5, level=0.4).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_route_level_verified", index=1, dest_index=0, level=0.4)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
