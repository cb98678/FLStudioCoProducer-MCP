def test_sets_position(rig):
    r = rig.call("set_song_position_verified", position=12.5)
    assert r.ok and r.meta["verified"] is True and rig.fake.transport["pos"] == 12.5


def test_failures(rig):
    assert rig.call("set_song_position_verified", position=-1).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("set_song_position_verified", position=3.0).error.code == "E_NOT_VERIFIED"
