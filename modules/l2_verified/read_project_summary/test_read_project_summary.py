def test_counts_match_fake(rig):
    r = rig.call("read_project_summary")
    assert r.ok
    assert r.value == {"project": "fake_project", "mixer_tracks": 6, "channels": 3, "patterns_with_data": 0,
                       "playlist_tracks": 5, "tempo": 140.0}


def test_reports_read_failure(rig):
    del rig.fake.modules["patterns"].patternCount
    r = rig.call("read_project_summary")
    assert not r.ok and r.error.code == "E_INTERNAL"
