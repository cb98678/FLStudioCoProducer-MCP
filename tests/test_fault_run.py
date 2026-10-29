"""E5: the dispatcher stops answering in the middle of a run. The run pauses in waiting_for_fl and resumes cleanly."""
from __future__ import annotations

import pytest

from coproducer import bridge
from coproducer.bridge import BridgeClient
from coproducer.fakefl import FakeFL
from coproducer.loopback import LoopbackTransport, load_device_script
from coproducer.orchestrator import executor
from coproducer.orchestrator.collab import ScriptedCollab
from coproducer.orchestrator.session import new_session
from coproducer.services import clear_services
from coproducer.testrig import MODULES


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "READ_TIMEOUT_S", 0.05)
    monkeypatch.setattr(bridge, "WRITE_TIMEOUT_S", 0.05)
    fake = FakeFL()
    script = load_device_script(fake)
    transport = LoopbackTransport(fake, script)
    made = {}

    def build(collab=None):
        s = new_session(MODULES, tmp_path / "run", collab or ScriptedCollab(approve_all=True))
        BridgeClient(s.registry, transport).attach(s.registry)
        s.registry.activate()
        made["s"] = s
        return s
    build.fake, build.transport = fake, transport
    yield build
    fake.uninstall()
    clear_services()


def plan():
    return {"plan_id": "e5", "steps": [
        {"id": "s01", "phase": "P4", "module": "set_track_volume_db_verified", "args": {"index": 1, "db": -6.0}, "verifier": "readback"},
        {"id": "s02", "phase": "P4", "module": "get_track_peak_db", "args": {"index": 1}, "verifier": "none"},
        {"id": "s03", "phase": "P4", "module": "set_track_volume_db_verified", "args": {"index": 2, "db": -9.0}, "verifier": "readback"},
        {"id": "s04", "phase": "P4", "module": "set_track_volume_db_verified", "args": {"index": 3, "db": -12.0}, "verifier": "readback"},
    ]}


def go_silent_after(world, session, n_steps):
    """Make the dispatcher stop answering once n_steps results are in the ledger."""
    real = session.ledger.append

    def watch(type_, **kw):
        out = real(type_, **kw)
        if type_ == "verify" and sum(1 for e in session.ledger.entries() if e["type"] == "verify") >= n_steps:
            world.transport.silent = True
        return out
    session.ledger.append = watch


def test_dispatcher_goes_silent_mid_run_and_the_run_pauses_then_resumes(world):
    s = world()
    go_silent_after(world, s, 2)                       # s01 and s02 finish, then FL stops answering
    r = executor.run_plan(s, plan())
    assert not r.ok and r.error.code == "E_TIMEOUT" and r.error.detail["status"] == "waiting_for_fl"
    assert r.error.detail["stopped_at"] == "s03" and r.error.detail["completed"] == ["s01", "s02"]
    assert r.error.detail["outcome_known"] is True       # a verified volume write can be repeated safely
    assert "Start FL Studio" in r.error.message and "coproducer resume" in r.error.message
    kinds = [e["type"] for e in s.ledger.entries()]
    assert kinds.count("waiting_for_fl") == 1 and "rollback" not in kinds and "ask" not in kinds
    assert s.waiting == "waiting_for_fl"

    # still silent: resuming does nothing and says so again
    s2 = world()
    writes_before = len(world.fake.calls("mixer", "setTrackVolume"))
    again = executor.run_plan(s2, plan())
    assert not again.ok and again.error.detail["status"] == "waiting_for_fl"
    assert len(world.fake.calls("mixer", "setTrackVolume")) == writes_before

    # FL comes back: the rest runs, and the two verified steps are not repeated
    world.transport.silent = False
    s3 = world()
    done = executor.run_plan(s3, plan())
    assert done.ok and done.value["resumed"] == ["s01", "s02"] and done.value["completed"] == ["s03", "s04"]
    assert len(world.fake.calls("mixer", "setTrackVolume")) == writes_before + 2
    assert [e["type"] for e in s3.ledger.entries()].count("resume_after_wait") == 1


def test_a_lost_reply_is_not_mistaken_for_a_dead_fl(world):
    """One read times out (its replies are lost) but FL still answers a ping, so the normal failure path runs: an offer to stop or roll back."""
    from coproducer.result import fail
    s = world(ScriptedCollab(answers=["stop here"], approve_all=True))
    real_proxy, real_append = s.registry.fl_proxy, s.ledger.append
    state = {"lose": False}
    ping_ops = ("op_general_get_version", "op_ui_get_version", "op_ui_get_prog_title")

    def flaky(name, kwargs):
        if state["lose"] and name not in ping_ops:
            return fail("E_TIMEOUT", "no reply from FL", retryable=True)
        return real_proxy(name, kwargs)

    def after_first_step(type_, **kw):
        out = real_append(type_, **kw)
        if type_ == "verify" and kw.get("step_id") == "s01":
            state["lose"] = True
        return out
    s.registry.fl_proxy = flaky
    s.ledger.append = after_first_step
    r = executor.run_plan(s, plan())
    assert not r.ok and r.error.code == "E_TIMEOUT" and r.error.detail["stopped_at"] == "s02", r
    assert r.error.detail.get("status") != "waiting_for_fl"
    kinds = [e["type"] for e in s.ledger.entries()]
    assert "waiting_for_fl" not in kinds and "ask" in kinds


def test_a_write_that_may_or_may_not_have_happened_asks_before_repeating(world):
    p = {"plan_id": "e5b", "steps": [
        {"id": "s01", "phase": "P4", "module": "add_time_marker_verified", "args": {"time": 1.0, "name": "drop"}, "verifier": "readback"}]}
    for choice, expect_ok in (("run it again", True), ("stop here", False)):
        s = world(ScriptedCollab(answers=[choice], approve_all=True))
        world.transport.silent = True
        r = executor.run_plan(s, p)
        assert not r.ok and r.error.detail["status"] == "waiting_for_fl" and r.error.detail["outcome_known"] is False
        world.transport.silent = False
        s2 = world(ScriptedCollab(answers=[choice], approve_all=True))
        out = executor.run_plan(s2, p)
        assert out.ok is expect_ok, (choice, out)
        if not expect_ok:
            assert out.error.code == "E_HALTED"
        # fresh run folder for the second round
        import shutil
        shutil.rmtree(s.run_dir, ignore_errors=True)
