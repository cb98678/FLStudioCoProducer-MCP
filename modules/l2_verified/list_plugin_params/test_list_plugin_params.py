def test_lists_named_params(rig):
    r = rig.call("list_plugin_params", index=0)
    assert r.ok and r.value["count"] == 8 and r.value["next"] is None
    assert [p["name"] for p in r.value["params"]] == ["Cutoff", "Resonance", "Drive", "Attack", "Release", "Mix"]
    page = rig.call("list_plugin_params", index=0, offset=0, limit=2).value
    assert page["next"] == 2 and len(page["params"]) == 2


def test_missing_plugin_fails(rig):
    assert rig.call("list_plugin_params", index=5).error.code == "E_ARG"
