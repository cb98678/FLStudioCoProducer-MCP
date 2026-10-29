def test_applies_bands(rig):
    r = rig.call("apply_eq_recipe", index=2, bands=[{"band": 0, "gain": 0.3, "freq": 0.2}, {"band": 2, "gain": 0.7, "bandwidth": 0.4}])
    assert r.ok and r.meta["verified"] is True and r.value == {"values_set": 4}
    eq = rig.fake.mixer[2]["eq"]
    assert (eq[0]["gain"], eq[0]["freq"], eq[2]["gain"], eq[2]["bw"]) == (0.3, 0.2, 0.7, 0.4)


def test_failures(rig):
    assert rig.call("apply_eq_recipe", index=2, bands=[{"band": 5, "gain": 0.3}]).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("apply_eq_recipe", index=2, bands=[{"band": 0, "gain": 0.3}]).error.code == "E_NOT_VERIFIED"
