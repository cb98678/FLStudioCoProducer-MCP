"""Tests for set_track_pan_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_track_pan_verified", index=1, pan=-0.25)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.mixer[1]['pan'] - -0.25) < 1e-9
    assert rig.fake.calls("mixer", "setTrackPan")


def test_failures(rig):
    assert rig.call("set_track_pan_verified", index=99, pan=0.1).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_track_pan_verified", index=1, pan=-0.25)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
