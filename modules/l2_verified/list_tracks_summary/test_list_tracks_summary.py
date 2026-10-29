def test_lists_all_tracks(rig):
    rig.fake.mixer[2]["name"] = "Bass"
    r = rig.call("list_tracks_summary")
    assert r.ok and len(r.value) == 6 and r.meta["total"] == 6
    assert r.value[2]["name"] == "Bass" and r.value[1]["volume"] == 0.8 and r.value[1]["volume_db"] == 0.0
    named = rig.call("list_tracks_summary", only_named=True).value
    assert [t["name"] for t in named] == ["Bass"]
    assert [t["index"] for t in rig.call("list_tracks_summary", start=3, count=2).value] == [3, 4]


def test_surfaces_read_error(rig):
    rig.fake.modules["mixer"].getTrackPan = lambda index: 1 / 0
    r = rig.call("list_tracks_summary")
    assert not r.ok and r.error.code == "E_INTERNAL"
