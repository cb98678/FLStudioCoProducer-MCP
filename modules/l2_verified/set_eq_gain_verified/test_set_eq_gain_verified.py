"""Tests for set_eq_gain_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_eq_gain_verified", index=1, band=0, value=0.7)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.mixer[1]['eq'][0]['gain'] - 0.7) < 1e-9
    assert rig.fake.calls("mixer", "setEqGain")


def test_failures(rig):
    assert rig.call("set_eq_gain_verified", index=99, band=0, value=0.7).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_eq_gain_verified", index=1, band=0, value=0.7)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
