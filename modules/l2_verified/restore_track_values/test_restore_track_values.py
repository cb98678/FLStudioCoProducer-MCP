def test_restores_changed_values(rig):
    snap = rig.call("snapshot_state").value
    rig.fake.mixer[1].update(volume=0.2, pan=0.5, mute=True, name="X")
    rig.fake.mixer[2]["solo"] = True
    r = rig.call("restore_track_values", snapshot=snap)
    assert r.ok and r.meta["verified"] is True and r.value == {"applied": 5}
    assert rig.call("snapshot_tracks").value == snap["tracks"]


def test_reports_values_that_do_not_stick(rig):
    snap = rig.call("snapshot_state").value
    rig.fake.mixer[1]["volume"] = 0.2
    rig.fake.ignore_writes = True
    r = rig.call("restore_track_values", snapshot=snap)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED" and r.error.detail["failed"][0]["path"] == "1.volume"
