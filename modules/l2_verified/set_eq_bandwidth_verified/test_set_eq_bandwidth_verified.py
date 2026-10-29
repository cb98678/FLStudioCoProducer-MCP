"""Tests for set_eq_bandwidth_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("set_eq_bandwidth_verified", index=1, band=2, value=0.65)
    assert r.ok and r.meta["verified"] is True
    assert abs(rig.fake.mixer[1]['eq'][2]['bw'] - 0.65) < 1e-9
    assert rig.fake.calls("mixer", "setEqBandwidth")


def test_failures(rig):
    assert rig.call("set_eq_bandwidth_verified", index=99, band=0, value=0.7).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("set_eq_bandwidth_verified", index=1, band=2, value=0.65)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
