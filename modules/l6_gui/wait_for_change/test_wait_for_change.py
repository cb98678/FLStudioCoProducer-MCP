def test_detects_a_change(rig, desk):
    calls = {"n": 0}
    real = desk.fake.grab

    def grab(rect):
        calls["n"] += 1
        desk.fake.frame = 0 if calls["n"] < 3 else 3
        return real(rect)
    desk.fake.grab = grab
    r = rig.call("wait_for_change", timeout_s=3, poll_s=0.01)
    assert r.ok and r.value["changed"] is True and r.value["fraction"] > 0.9


def test_times_out_without_error(rig, desk):
    r = rig.call("wait_for_change", timeout_s=0.1, poll_s=0.02)
    assert r.ok and r.value["changed"] is False
    desk.halt.flag = True
    assert rig.call("wait_for_change").error.code == "E_HALTED"
