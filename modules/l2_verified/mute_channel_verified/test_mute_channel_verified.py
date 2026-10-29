"""Tests for mute_channel_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("mute_channel_verified", index=1, muted=True)
    assert r.ok and r.meta["verified"] is True
    assert rig.fake.channels[1]['mute'] == True
    assert rig.fake.calls("channels", "muteChannel")


def test_failures(rig):
    assert rig.call("mute_channel_verified", index=99, muted=True).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("mute_channel_verified", index=1, muted=True)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
