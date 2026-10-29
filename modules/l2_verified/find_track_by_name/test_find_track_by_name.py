def test_finds_matches(rig):
    rig.fake.mixer[2]["name"] = "Sub Bass"
    rig.fake.mixer[3]["name"] = "bass layer"
    r = rig.call("find_track_by_name", pattern="BASS")
    assert [h["index"] for h in r.value] == [2, 3]
    assert [h["index"] for h in rig.call("find_track_by_name", pattern="BASS", ignore_case=False).value] == []


def test_missing_name_is_empty(rig):
    assert rig.call("find_track_by_name", pattern="zzz").value == []
    assert rig.call("find_track_by_name", pattern="").error.code == "E_ARG"
