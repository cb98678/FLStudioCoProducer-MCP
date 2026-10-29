def test_captures_channels(rig):
    r = rig.call("snapshot_channels")
    assert r.ok and r.value["2"] == {"name": "Channel 2", "volume": 0.78, "pan": 0.0, "mute": False, "target": 0}


def test_surfaces_read_error(rig):
    rig.fake.modules["channels"].getTargetFxTrack = lambda *a: 1 / 0
    assert rig.call("snapshot_channels").error.code == "E_INTERNAL"
