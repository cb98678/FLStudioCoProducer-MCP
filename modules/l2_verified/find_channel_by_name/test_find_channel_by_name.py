def test_finds_matches(rig):
    rig.fake.channels[2]["name"] = "Lead Saw"
    assert rig.call("find_channel_by_name", pattern="lead").value == [{"index": 2, "name": "Lead Saw"}]
    assert rig.call("find_channel_by_name", pattern="lead", ignore_case=False).value == []


def test_empty_pattern_rejected(rig):
    assert rig.call("find_channel_by_name", pattern="").error.code == "E_ARG"
