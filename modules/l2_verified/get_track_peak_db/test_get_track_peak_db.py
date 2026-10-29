def test_converts_to_db(rig):
    rig.fake.mixer[1]["src"] = 0.5
    r = rig.call("get_track_peak_db", index=1)
    assert r.ok and abs(r.value["db"] - (-6.02 + 0.0)) < 0.05
    assert rig.call("get_track_peak_db", index=2).value["db"] == -120.0


def test_rejects_bad_index(rig):
    assert rig.call("get_track_peak_db", index=99).error.code == "E_ARG"
    assert rig.call("get_track_peak_db", index=-1).error.code == "E_ARG"
