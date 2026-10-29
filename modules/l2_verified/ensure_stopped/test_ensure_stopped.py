def test_stops_once(rig):
    first = rig.call("ensure_stopped")
    assert first.meta["verified"] is True and first.meta["changed"] is False
    rig.fake.transport["playing"] = True
    r = rig.call("ensure_stopped")
    assert r.ok and r.meta["changed"] is True and rig.fake.transport["playing"] is False


def test_reports_a_stop_that_does_not_happen(rig):
    rig.fake.transport["playing"] = True
    rig.fake.ignore_writes = True
    r = rig.call("ensure_stopped", wait_s=0.1)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
