def test_snapshot_has_all_parts(rig):
    r = rig.call("snapshot_state")
    assert r.ok and set(r.value) == {"tracks", "channels", "tempo"} and r.value["tempo"] == 140.0
    assert set(rig.call("snapshot_state", include_channels=False).value) == {"tracks", "tempo"}


def test_surfaces_read_error(rig):
    rig.fake.modules["mixer"].getCurrentTempo = lambda *a: 1 / 0
    assert rig.call("snapshot_state").error.code == "E_INTERNAL"
