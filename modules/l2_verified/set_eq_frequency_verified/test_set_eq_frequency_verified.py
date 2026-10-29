"""Tests for set_eq_frequency_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_eq_frequency_verified", index=1, band=1, value=0.3)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.mixer[1]['eq'][1]['freq'] - 0.3) < 1e-9
    assert rig.fake.calls("mixer", "setEqFrequency")


def test_failures(rig):
    assert rig.call("set_eq_frequency_verified", index=99, band=0, value=0.7).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_eq_frequency_verified", index=1, band=1, value=0.3)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
