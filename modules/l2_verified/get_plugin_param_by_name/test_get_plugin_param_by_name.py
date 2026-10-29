def test_reads_by_name(rig):
    rig.fake.plugins[(0, -1)]["params"][2][1] = 0.25
    r = rig.call("get_plugin_param_by_name", index=0, name="Drive")
    assert r.ok and r.value == {"param": 2, "value": 0.25, "text": "0.250"}


def test_unknown_and_ambiguous(rig):
    r = rig.call("get_plugin_param_by_name", index=0, name="Nope")
    assert r.error.code == "E_NOT_FOUND" and "Drive" in r.error.detail["known"]
    rig.fake.plugins[(0, -1)]["params"][1][0] = "Cutoff"
    rig.call("build_param_map", index=0, refresh=True)  # the map is cached per plugin name
    assert rig.call("get_plugin_param_by_name", index=0, name="Cutoff").error.code == "E_ARG"
