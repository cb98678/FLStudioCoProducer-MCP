def test_toggles_only_when_needed(rig):
    first = rig.call("ensure_loop_mode", song=False)
    assert first.meta["verified"] is True and first.meta["changed"] is False
    r = rig.call("ensure_loop_mode", song=True)
    assert r.ok and r.value == 1 and r.meta["changed"] is True
    assert rig.call("ensure_loop_mode", song=True).meta["changed"] is False
    assert len(rig.fake.calls("transport", "setLoopMode")) == 1


def test_reports_ignored_toggle(rig):
    rig.fake.ignore_writes = True
    assert rig.call("ensure_loop_mode", song=True).error.code == "E_NOT_VERIFIED"
