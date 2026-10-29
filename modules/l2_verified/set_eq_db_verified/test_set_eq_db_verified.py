def test_db_maps_to_raw_and_reads_back(rig):
    r = rig.call("set_eq_db_verified", index=0, band=2, db=-4.65)
    assert r.ok and abs(r.value - 0.35) < 1e-6 and r.meta["verified"] is True
    assert abs(rig.fake.mixer[0]["eq"][2]["gain"] - 0.35) < 1e-6
    assert rig.call("set_eq_db_verified", index=0, band=2, db=0).value == 0.5


def test_rejects_bad_band_and_range(rig):
    assert rig.call("set_eq_db_verified", index=0, band=3, db=1).error.code == "E_ARG"
    assert not rig.call("set_eq_db_verified", index=0, band=1, db=20).ok
