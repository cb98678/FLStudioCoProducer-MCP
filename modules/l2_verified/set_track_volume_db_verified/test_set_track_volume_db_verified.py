import math


def test_converges_even_with_a_different_fader_law(rig):
    r = rig.call("set_track_volume_db_verified", index=2, db=-6.0)
    assert r.ok and r.meta["verified"] is True and abs(r.value + 6.0) <= 0.15 and r.meta["writes"] == 1
    rig.fake.db_law = lambda v: 30 * math.log10(v / 0.8)
    r = rig.call("set_track_volume_db_verified", index=3, db=-6.0)
    assert r.ok and abs(r.value + 6.0) <= 0.15 and 1 < r.meta["writes"] <= 5 and r.meta["verified"] is True


def test_failures(rig):
    assert rig.call("set_track_volume_db_verified", index=1, db=-100).error.code == "E_ARG"
    assert rig.call("set_track_volume_db_verified", index=99, db=-3).error.code == "E_ARG"
    assert rig.call("set_track_volume_db_verified", index=1, db=6.0).error.code == "E_NOT_VERIFIED"  # above the fader top
    rig.fake.ignore_writes = True
    assert rig.call("set_track_volume_db_verified", index=1, db=-3.0).error.code == "E_NOT_VERIFIED"
