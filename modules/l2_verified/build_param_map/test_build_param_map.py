def test_builds_and_caches(rig):
    r = rig.call("build_param_map", index=0)
    assert r.ok and r.value["map"]["Drive"] == 2 and r.meta["cached"] is False
    assert rig.call("build_param_map", index=0).meta["cached"] is True
    assert rig.call("build_param_map", index=0, refresh=True).meta["cached"] is False


def test_duplicates_and_missing(rig):
    rig.fake.plugins[(0, -1)]["params"][1][0] = "Cutoff"
    r = rig.call("build_param_map", index=0)
    assert r.value["duplicates"] == {"Cutoff": [0, 1]} and "Cutoff" not in r.value["map"]
    assert rig.call("build_param_map", index=7).error.code == "E_ARG"
