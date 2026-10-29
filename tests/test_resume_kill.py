"""G2-4: kill the orchestrator process hard in the middle of a run, start it again, and no verified step is repeated.

The child process runs a plan of many verified volume writes against a fake FL. The parent kills it (SIGKILL / TerminateProcess,
no cleanup code runs) once the ledger shows some steps done. A second child resumes the same run folder and the same FL state
(the fake FL state is carried in a JSON file, as FL itself would keep it) and the test counts the writes each child made.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

N_STEPS = 24

CHILD = textwrap.dedent('''
    import json, sys, time
    from pathlib import Path
    from coproducer.bridge import BridgeClient
    from coproducer.fakefl import FakeFL
    from coproducer.loopback import LoopbackTransport, load_device_script
    from coproducer.orchestrator import executor
    from coproducer.orchestrator.collab import ScriptedCollab
    from coproducer.orchestrator.ledger import Ledger
    from coproducer.orchestrator.session import new_session
    from coproducer.testrig import MODULES

    run_dir, state_file, out_file, slow = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), float(sys.argv[4])
    fake = FakeFL()
    if state_file.exists():
        for k, v in enumerate(json.loads(state_file.read_text())):
            fake.mixer[k]["volume"] = v
    script = load_device_script(fake)
    s = new_session(MODULES, run_dir, ScriptedCollab(approve_all=True))
    BridgeClient(s.registry, LoopbackTransport(fake, script)).attach(s.registry)
    s.registry.activate()
    real_append = Ledger.append
    def slow_append(self, type_, **kw):
        out = real_append(self, type_, **kw)
        if type_ == "step_result" and slow:
            time.sleep(slow)
        return out
    Ledger.append = slow_append
    steps = [{"id": "s%02d" % i, "phase": "P4", "module": "set_track_volume_db_verified",
              "args": {"index": 1 + (i % 3), "db": -3.0 - i * 0.25}, "verifier": "readback"} for i in range(__N__)]
    r = executor.run_plan(s, {"plan_id": "kill", "steps": steps})
    writes = [c for c in fake.calls("mixer", "setTrackVolume")]
    out_file.write_text(json.dumps({"ok": r.ok, "completed": r.value["completed"] if r.ok else None,
                                    "resumed": r.value["resumed"] if r.ok else None, "writes": len(writes),
                                    "error": None if r.ok else r.error.code}))
    state_file.write_text(json.dumps([t["volume"] for t in fake.mixer]))
''').replace("__N__", str(N_STEPS))


def _done_steps(run_dir: Path) -> list:
    """Steps the ledger counts as done: result ok and verification passed. A kill between the two leaves a step not done."""
    from coproducer.orchestrator.ledger import Ledger
    ledger = run_dir / "ledger.jsonl"
    return sorted(Ledger(ledger).done_steps()) if ledger.is_file() else []


def test_hard_kill_in_the_middle_then_resume_repeats_no_verified_step(tmp_path):
    run_dir = tmp_path / "run"
    state, out1, out2 = tmp_path / "state.json", tmp_path / "out1.json", tmp_path / "out2.json"
    child = tmp_path / "child.py"
    child.write_text(CHILD)
    p = subprocess.Popen([sys.executable, str(child), str(run_dir), str(state), str(out1), "0.15"], stderr=subprocess.PIPE)
    deadline = time.time() + 120
    while time.time() < deadline and len(_done_steps(run_dir)) < 6 and p.poll() is None:
        time.sleep(0.05)
    assert p.poll() is None, ("child ended before it could be killed", p.stderr.read().decode()[-800:])
    p.kill()                                   # no signal handler, no finally blocks, no flush
    p.wait(timeout=30)
    killed_after = _done_steps(run_dir)
    assert 6 <= len(killed_after) < N_STEPS and not out1.exists(), killed_after

    again = subprocess.run([sys.executable, str(child), str(run_dir), str(state), str(out2), "0"], capture_output=True, text=True, timeout=300)
    assert again.returncode == 0, again.stderr[-1500:]
    r = json.loads(out2.read_text())
    assert r["ok"], r
    assert sorted(r["resumed"]) == killed_after and len(r["completed"]) == N_STEPS - len(killed_after), (r, killed_after)
    # the second process wrote only the steps that were not verified before the kill
    assert r["writes"] == N_STEPS - len(killed_after), r
    assert sorted(_done_steps(run_dir)) == sorted(f"s{i:02d}" for i in range(N_STEPS))
