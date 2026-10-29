"""Tests for set_track_volume_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_track_volume_verified", index=1, volume=0.5)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.mixer[1]['volume'] - 0.5) < 1e-9
    assert rig.fake.calls("mixer", "setTrackVolume")


def test_failures(rig):
    assert rig.call("set_track_volume_verified", index=99, volume=0.5).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_track_volume_verified", index=1, volume=0.5)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
