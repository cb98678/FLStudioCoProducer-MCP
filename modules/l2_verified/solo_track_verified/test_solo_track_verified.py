"""Tests for solo_track_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("solo_track_verified", index=1, solo=True)
    assert r.ok and r.meta["verified"] is True
    assert rig.fake.mixer[1]['solo'] == True
    assert rig.fake.calls("mixer", "soloTrack")


def test_failures(rig):
    assert rig.call("solo_track_verified", index=99, solo=True).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("solo_track_verified", index=1, solo=True)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
