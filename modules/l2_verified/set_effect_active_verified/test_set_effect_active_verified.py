def test_toggles_and_reads_back(rig):
    r = rig.call("set_effect_active_verified", index=1, slot_index=0, active=False)
    assert r.ok and r.value is False and r.meta["verified"] is True
    assert rig.fake.plugins[(1, 0)]["mute"] == 0
    assert rig.call("set_effect_active_verified", index=1, slot_index=0, active=True).value is True


def test_failures(rig):
    assert not rig.call("set_effect_active_verified", index=1, slot_index=9, active=True).ok
    rig.fake.ignore_writes = True
    r = rig.call("set_effect_active_verified", index=1, slot_index=0, active=False)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
