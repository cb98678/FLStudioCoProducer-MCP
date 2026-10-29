def test_toggles_only_when_needed(rig):
    assert rig.call("solo_channel_verified", index=1, solo=False).meta["changed"] is False
    r = rig.call("solo_channel_verified", index=1, solo=True)
    assert r.ok and r.meta["changed"] is True and rig.fake.channels[1]["solo"] is True
    assert rig.call("solo_channel_verified", index=1, solo=True).meta["changed"] is False


def test_failures(rig):
    assert rig.call("solo_channel_verified", index=99, solo=True).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("solo_channel_verified", index=1, solo=True).error.code == "E_NOT_VERIFIED"
