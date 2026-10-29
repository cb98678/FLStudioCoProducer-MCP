def test_restores_everything(rig):
    snap = rig.call("snapshot_state").value
    rig.fake.mixer[3]["volume"] = 0.1
    rig.fake.channels[0]["pan"] = -0.5
    rig.fake.tempo = 128.0
    r = rig.call("restore_state_values", snapshot=snap)
    assert r.ok and r.meta["verified"] is True and r.value == {"applied": 3}
    assert rig.call("snapshot_state").value == snap


def test_stops_when_a_part_fails(rig):
    snap = rig.call("snapshot_state").value
    rig.fake.mixer[3]["volume"] = 0.1
    rig.fake.ignore_writes = True
    r = rig.call("restore_state_values", snapshot=snap)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
