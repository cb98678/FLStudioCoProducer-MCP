def test_rolls_back_and_proves_it(rig):
    snap = rig.call("snapshot_state").value
    rig.call("set_track_volume_verified", index=2, volume=0.1)
    rig.call("mute_channel_verified", index=0, muted=True)
    r = rig.call("rollback_to", snapshot=snap)
    assert r.ok and r.meta["verified"] is True and r.value == {"applied": 2}
    assert rig.call("snapshot_state").value == snap


def test_reports_what_cannot_be_restored(rig):
    snap = rig.call("snapshot_state").value
    snap["tracks"]["2"]["volume"] = 0.8
    rig.fake.mixer[2]["volume"] = 0.3
    rig.fake.ignore_writes = True
    assert rig.call("rollback_to", snapshot=snap).error.code == "E_NOT_VERIFIED"
