"""Tests for set_channel_pan_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_channel_pan_verified", index=1, pan=0.3)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.channels[1]['pan'] - 0.3) < 1e-9
    assert rig.fake.calls("channels", "setChannelPan")


def test_failures(rig):
    assert rig.call("set_channel_pan_verified", index=99, pan=0.3).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_channel_pan_verified", index=1, pan=0.3)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
