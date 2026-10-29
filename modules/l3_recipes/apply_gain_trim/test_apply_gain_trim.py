def test_applies_and_caps_the_step(rig):
    r = rig.call("apply_gain_trim", index=2, delta_db=-3.0)
    assert r.ok and r.meta["verified"] is True and r.value["capped"] is False
    assert abs(r.value["after_db"] + 3.0) <= 0.15
    big = rig.call("apply_gain_trim", index=2, delta_db=-20.0, max_delta_db=4.0)
    assert big.value["capped"] is True and big.value["applied_delta_db"] == -4.0
    assert abs(big.value["after_db"] - (r.value["after_db"] - 4.0)) <= 0.3


def test_failures(rig):
    assert rig.call("apply_gain_trim", index=99, delta_db=-1).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    assert rig.call("apply_gain_trim", index=1, delta_db=-3).error.code == "E_NOT_VERIFIED"


def test_stops_at_the_top_of_the_fader(rig):
    r = rig.call("apply_gain_trim", index=2, delta_db=6.0)
    assert r.ok and r.value["capped"] is True and r.value["after_db"] <= 5.6 and r.value["applied_delta_db"] < 6.0
