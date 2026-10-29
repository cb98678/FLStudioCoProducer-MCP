"""Tests for set_playlist_track_name_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_playlist_track_name_verified", index=2, name='Drums')
    assert r.ok and r.meta["verified"] is True
    assert rig.fake.playlist[1]['name'] == 'Drums'
    assert rig.fake.calls("playlist", "setTrackName")


def test_failures(rig):
    assert rig.call("set_playlist_track_name_verified", index=99, name='x').error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_playlist_track_name_verified", index=2, name='Drums')
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
