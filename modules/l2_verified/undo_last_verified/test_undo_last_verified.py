def test_undo_reverts_a_change(rig):
    rig.call("set_track_volume_verified", index=2, volume=0.3)
    r = rig.call("undo_last_verified")
    assert r.ok and r.meta["verified"] is True
    assert r.value == [{"path": "2.volume", "before": 0.3, "after": 0.8}]
    assert rig.fake.mixer[2]["volume"] == 0.8


def test_nothing_to_undo(rig):
    r = rig.call("undo_last_verified")
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
