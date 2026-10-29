def test_lists_channels(rig):
    rig.fake.channels[1]["target"] = 4
    r = rig.call("list_channels_summary")
    assert r.ok and [c["index"] for c in r.value] == [0, 1, 2]
    assert r.value[1]["target_track"] == 4 and r.value[0]["name"] == "Channel 0" and r.value[0]["muted"] is False


def test_surfaces_read_error(rig):
    rig.fake.modules["channels"].getChannelType = lambda *a: 1 / 0
    assert rig.call("list_channels_summary").error.code == "E_INTERNAL"
