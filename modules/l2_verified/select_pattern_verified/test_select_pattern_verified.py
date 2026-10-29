"""Tests for select_pattern_verified: golden against the fake FL, and failure handling."""


def test_reads_back_and_changes_fake(rig):
    r = rig.call("select_pattern_verified", index=3)
    assert r.ok and r.meta["verified"] is True
    assert rig.fake.pattern_current == 3
    assert rig.fake.calls("patterns", "jumpToPattern")


def test_failures(rig):
    assert rig.call("select_pattern_verified", index=99).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("select_pattern_verified", index=3)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
