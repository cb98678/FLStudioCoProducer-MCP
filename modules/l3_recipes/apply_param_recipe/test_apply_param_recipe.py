def test_sets_named_params(rig):
    r = rig.call("apply_param_recipe", index=0, params={"Cutoff": 0.2, "Drive": 0.9})
    assert r.ok and r.meta["verified"] is True and r.value == {"set": {"Cutoff": 0.2, "Drive": 0.9}}


def test_failures(rig):
    assert rig.call("apply_param_recipe", index=0, params={"Nope": 0.2}).error.code == "E_NOT_FOUND"
    assert rig.call("apply_param_recipe", index=0, params={"Cutoff": 2}).error.code == "E_ARG"
