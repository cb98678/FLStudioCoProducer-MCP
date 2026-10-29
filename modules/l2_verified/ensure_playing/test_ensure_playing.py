def test_starts_once(rig):
    r = rig.call("ensure_playing")
    assert r.ok and r.meta == {"verified": True, "changed": True} and rig.fake.transport["playing"] is True
    r = rig.call("ensure_playing")
    assert r.ok and r.meta["changed"] is False and len(rig.fake.calls("transport", "start")) == 1


def test_reports_a_start_that_does_not_happen(rig):
    rig.fake.ignore_writes = True
    r = rig.call("ensure_playing", wait_s=0.1)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
