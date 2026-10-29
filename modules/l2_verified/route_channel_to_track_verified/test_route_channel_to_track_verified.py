"""Tests for route_channel_to_track_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("route_channel_to_track_verified", channel_index=1, track_index=3)
    assert r.ok and r.meta["verified"] is True
    assert rig.fake.channels[1]['target'] == 3
    assert rig.fake.calls("channels", "setTargetFxTrack")


def test_failures(rig):
    assert rig.call("route_channel_to_track_verified", channel_index=1, track_index=99).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("route_channel_to_track_verified", channel_index=1, track_index=3)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
