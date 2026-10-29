def test_sets_by_name(rig):
    r = rig.call("set_plugin_param_by_name", index=0, name="Cutoff", value=0.9)
    assert r.ok and r.meta["verified"] is True and r.meta["param"] == 0
    assert rig.fake.plugins[(0, -1)]["params"][0][1] == 0.9
    r = rig.call("set_plugin_param_by_name", index=1, slot_index=0, name="Mid", value=0.1)
    assert r.ok and rig.fake.plugins[(1, 0)]["params"][1][1] == 0.1


def test_failures(rig):
    assert rig.call("set_plugin_param_by_name", index=0, name="Nope", value=0.5).error.code == "E_NOT_FOUND"
    assert rig.call("set_plugin_param_by_name", index=0, name="Cutoff", value=1.5).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("set_plugin_param_by_name", index=0, name="Cutoff", value=0.9).error.code == "E_NOT_VERIFIED"
