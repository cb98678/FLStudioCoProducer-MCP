def test_trims_each_stage_toward_its_target(rig):
    rig.fake.mixer[1]["src"] = 0.9
    rig.fake.mixer[2]["src"] = 0.2
    r = rig.call("stage_gain_chain", hold_s=0.0, stages=[{"index": 1, "target_peak_db": -6.0}, {"index": 2, "target_peak_db": -12.0}])
    assert r.ok and r.meta["verified"] is True
    after1 = rig.call("get_track_peak_db", index=1).value["db"]
    after2 = rig.call("get_track_peak_db", index=2).value["db"]
    assert abs(after1 + 6.0) < 0.3 and abs(after2 + 12.0) < 0.3


def test_silence_is_skipped_and_errors_surface(rig):
    r = rig.call("stage_gain_chain", hold_s=0.0, stages=[{"index": 3, "target_peak_db": -6.0}])
    assert r.ok and r.value["stages"] == [{"index": 3, "skipped": "silent"}]
    assert rig.call("stage_gain_chain", hold_s=0.0, stages=[{"index": 99, "target_peak_db": -6.0}]).error.code == "E_ARG"
