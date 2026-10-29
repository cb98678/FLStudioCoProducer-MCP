def test_captures_tracks(rig):
    r = rig.call("snapshot_tracks")
    assert r.ok and sorted(r.value, key=int) == ["0", "1", "2", "3", "4", "5"]
    assert r.value["1"] == {"name": "Insert 1", "volume": 0.8, "pan": 0.0, "stereo": 0.0, "mute": False, "solo": False}
    assert list(rig.call("snapshot_tracks", track_limit=2).value) == ["0", "1"]


def test_surfaces_read_error(rig):
    rig.fake.modules["mixer"].isTrackSolo = lambda i: 1 / 0
    assert rig.call("snapshot_tracks").error.code == "E_INTERNAL"
