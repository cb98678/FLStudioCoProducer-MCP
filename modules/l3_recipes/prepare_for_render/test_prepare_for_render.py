def test_stops_rewinds_and_reports_state(rig):
    rig.fake.transport.update(playing=True, pos=42.0, loop=1)
    rig.fake.changed = 1
    r = rig.call("prepare_for_render")
    assert r.ok and r.meta["verified"] is True
    assert r.value == {"was_playing": True, "position": 42.0, "loop_song": True, "unsaved": True}
    assert rig.fake.transport["playing"] is False and rig.fake.transport["pos"] == 0.0


def test_failures(rig):
    rig.fake.transport["playing"] = True
    rig.fake.ignore_writes = True
    assert rig.call("prepare_for_render").error.code == "E_NOT_VERIFIED"
