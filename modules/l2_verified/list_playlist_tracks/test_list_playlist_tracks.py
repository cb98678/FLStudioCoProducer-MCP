def test_lists_named_tracks(rig):
    rig.fake.playlist[1]["name"] = "Drums"
    assert rig.call("list_playlist_tracks").value == [{"index": 2, "name": "Drums", "muted": False}]
    assert len(rig.call("list_playlist_tracks", only_named=False).value) == 5
    assert len(rig.call("list_playlist_tracks", only_named=False, limit=2).value) == 2


def test_surfaces_read_error(rig):
    rig.fake.modules["playlist"].isTrackMuted = lambda i: 1 / 0
    assert rig.call("list_playlist_tracks").error.code == "E_INTERNAL"
