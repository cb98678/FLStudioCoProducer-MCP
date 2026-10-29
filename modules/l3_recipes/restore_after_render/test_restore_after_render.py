def test_restores_transport(rig):
    r = rig.call("restore_after_render", was_playing=True, position=42.0, loop_song=True)
    assert r.ok and r.meta["verified"] is True
    assert rig.fake.transport == {"playing": True, "recording": False, "loop": 1, "pos": 42.0}


def test_failures(rig):
    assert rig.call("restore_after_render", was_playing=True, position=-1.0, loop_song=False).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("restore_after_render", was_playing=False, position=5.0, loop_song=True).error.code == "E_NOT_VERIFIED"
