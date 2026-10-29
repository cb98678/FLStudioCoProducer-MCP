def test_restores_changed_values(rig):
    snap = rig.call("snapshot_state").value
    rig.fake.channels[1].update(volume=0.1, mute=True, target=4)
    r = rig.call("restore_channel_values", snapshot=snap)
    assert r.ok and r.meta["verified"] is True and r.value == {"applied": 3}
    assert rig.call("snapshot_channels").value == snap["channels"]


def test_reports_values_that_do_not_stick(rig):
    snap = rig.call("snapshot_state").value
    rig.fake.channels[1]["volume"] = 0.1
    rig.fake.ignore_writes = True
    r = rig.call("restore_channel_values", snapshot=snap)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED" and r.error.detail["failed"][0]["path"] == "1.volume"
