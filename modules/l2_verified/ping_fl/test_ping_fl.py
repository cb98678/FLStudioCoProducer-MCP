def test_reports_versions(rig):
    r = rig.call("ping_fl")
    assert r.ok and r.value == {"api": 45, "fl": "2026.1.7", "project": "fake_project"}


def test_reports_bridge_failure(rig):
    rig.transport.busy = 10**6
    rig.client.request = lambda *a, **k: __import__("coproducer.result", fromlist=["fail"]).fail("E_TIMEOUT", "no reply")
    r = rig.call("ping_fl")
    assert not r.ok and r.error.code == "E_TIMEOUT"
