"""Ledger, spec sheet, plan validation, verifiers and the executor against the fake FL."""
import json

from coproducer.orchestrator import executor, spec_sheet
from coproducer.orchestrator.collab import PendingCollab, ScriptedCollab
from coproducer.orchestrator.ledger import Ledger
from coproducer.orchestrator.plan import find_refs, resolve_args, validate_plan
from coproducer.orchestrator.session import check_original, record_original


def vol_plan(db=-6.0):
    return {"plan_id": "t1", "steps": [
        {"id": "s01", "phase": "P0", "module": "read_project_summary", "args": {}, "verifier": "none"},
        {"id": "s02", "phase": "P4", "module": "set_track_volume_db_verified", "args": {"index": 1, "db": db}, "verifier": "readback"},
        {"id": "s03", "phase": "P4", "module": "get_track_peak_db", "args": {"index": 1}, "verifier": "none"},
    ]}


# ---------------------------------------------------------------- ledger
def test_ledger_appends_and_survives_a_torn_line(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    led.append("run_start", goal="x")
    led.append("note", what="y")
    with open(led.path, "a") as f:
        f.write('{"seq": 3, "ty')                       # crash mid-write
    again = Ledger(led.path)
    assert [e["seq"] for e in again.entries()] == [1, 2] and again.seq == 2
    assert again.append("note", what="z")["seq"] == 3


def test_ledger_truncates_big_values_and_rejects_unknown_types(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    e = led.append("note", blob="x" * 100000)
    assert e["blob"]["_truncated"] is True and e["blob_complete"] is False
    try:
        led.append("bogus")
        raise AssertionError("should have raised")
    except ValueError:
        pass


# ---------------------------------------------------------------- spec sheet
def test_spec_roundtrip_decision_and_gaps(tmp_path):
    p = tmp_path / "specs" / "a" / "spec.md"
    assert spec_sheet.write_spec(p, {"project": "a", "mode": "restyle", "source": None, "iteration_cap": 3}).ok
    got = spec_sheet.read_spec(p).value
    assert got["header"] == {"project": "a", "mode": "restyle", "source": None, "iteration_cap": 3}
    assert spec_sheet.missing_fields(got["header"], "P1") == ["source"]
    assert spec_sheet.add_decision(p, "Use half-time", "dubstep feel", "2026-10-18").ok
    assert "- 2026-10-18: Use half-time. Reason: dubstep feel" in spec_sheet.read_spec(p).value["body"]
    assert spec_sheet.write_spec(p, {"mode": "bogus"}).error.code == "E_ARG"
    assert spec_sheet.read_spec(tmp_path / "none.md").error.code == "E_NOT_FOUND"
    assert spec_sheet.digest({"a": 1}, "x" * 5000, limit=100).endswith("...")


def test_spec_header_comments_are_ignored():
    h, body = spec_sheet.parse_spec("---\nmode: mix   # new | mix\ncap: 3\nrate: 0.5\n---\n# Goals\n")
    assert h == {"mode": "mix", "cap": 3, "rate": 0.5} and body == "# Goals\n"


# ---------------------------------------------------------------- plan
def test_plan_validation_collects_every_problem(run):
    s = run()
    mods = s.registry.modules
    assert validate_plan(vol_plan(), mods).ok
    bad = {"steps": [
        {"id": "a", "phase": "P9", "module": "nope", "verifier": "none"},
        {"id": "a", "phase": "P4", "module": "set_track_volume_db_verified", "args": {"index": "$z.value"}, "verifier": "none"},
        {"id": "c", "phase": "P4", "module": "set_track_volume_db_verified", "args": {}, "verifier": "readback", "autonomy": "A3"},
        {"id": "d", "phase": "P4", "module": "op_mixer_get_track_name", "args": {}, "verifier": "none"},
        {"id": "e", "phase": "P4", "module": "read_project_summary", "args": {}},
    ]}
    r = validate_plan(bad, mods)
    text = " | ".join(r.error.detail["problems"])
    assert r.error.code == "E_ARG"
    for needle in ("phase must be", "not registered", "repeated", "not an earlier step", "needs a real verifier",
                   "A3 is human only", "missing or unknown"):
        assert needle in text, needle
    assert validate_plan({"steps": []}, mods).error.code == "E_ARG"


def test_references_resolve_through_dicts_and_lists():
    results = {"s1": {"value": {"files": [{"path": "a.wav"}, {"path": "b.wav"}]}}}
    assert find_refs({"x": ["$s1.value.files.1.path", "plain"]}) == [("s1", "value.files.1.path")]
    assert resolve_args({"x": ["$s1.value.files.1.path", 5]}, results).value == {"x": ["b.wav", 5]}
    assert resolve_args("$s1.value.files.9", results).error.code == "E_NOT_FOUND"
    assert resolve_args("$s2.value", results).error.code == "E_NOT_FOUND"


# ---------------------------------------------------------------- executor
def test_plan_runs_verifies_and_records(run):
    s = run()
    r = executor.run_plan(s, vol_plan())
    assert r.ok and r.value["completed"] == ["s01", "s02", "s03"]
    types = [e["type"] for e in s.ledger.entries()]
    assert types.count("step_result") == 3 and types.count("verify") == 3 and types.count("phase_enter") == 2
    v = [e for e in s.ledger.entries() if e["type"] == "step_result" and e["step_id"] == "s02"][0]
    assert v["ok"] and v["verified"] is True
    assert abs(run.fake.mixer[1]["volume"] - 0.8 * 10 ** (-6 / 20)) < 0.02 or run.fake.calls("mixer", "setTrackVolume")


def test_failed_write_stops_asks_and_can_roll_back(run):
    collab = ScriptedCollab(answers=["roll back to snapshot start_P4"], approve_all=True)
    s = run(collab)
    run.fake.ignore_writes = False
    plan = vol_plan()
    plan["steps"][1]["risky"] = True
    run.fake.ignore_writes = True                    # FL silently ignores the write
    r = executor.run_plan(s, plan)
    assert not r.ok and r.error.code == "E_NOT_VERIFIED" and r.error.detail["stopped_at"] == "s02"
    assert r.error.detail["completed"] == ["s01"]
    assert "Step s02 failed" in collab.asked[0]["question"] and any("roll back" in o for o in collab.asked[0]["options"])
    assert [e["type"] for e in s.ledger.entries()].count("rollback") == 1


def test_resume_does_not_repeat_verified_steps(run, tmp_path):
    s = run(run_dir=tmp_path / "r1")
    first = vol_plan()
    assert executor.run_plan(s, {"steps": first["steps"][:2]}).ok
    writes = len(run.fake.calls("mixer", "setTrackVolume"))
    s2 = run(run_dir=tmp_path / "r1", fake=run.fake)           # new process, same ledger, same FL
    r = executor.run_plan(s2, first)
    assert r.ok and r.value["resumed"] == ["s01", "s02"] and r.value["completed"] == ["s03"]
    assert len(run.fake.calls("mixer", "setTrackVolume")) == writes


def test_a1_step_needs_approval_and_unattended_runs_write_pending_file(run, tmp_path):
    pending = tmp_path / "pending.json"
    s = run(PendingCollab(pending))
    plan = vol_plan()
    plan["steps"][0]["autonomy"] = "A1"
    r = executor.run_plan(s, plan)
    assert not r.ok and r.error.code == "E_PENDING_HUMAN" and r.error.detail["stopped_at"] == "s01"
    items = json.loads(pending.read_text())
    assert any("approve" in i for i in items) and any("question" in i for i in items)


def test_halt_stops_before_the_next_step(run):
    s = run()
    s.halt.set()
    r = executor.run_plan(s, vol_plan())
    assert not r.ok and r.error.code == "E_HALTED" and r.error.detail["stopped_at"] == "s01"


def test_phase_entry_needs_spec_fields(run, tmp_path):
    s = run()
    s.spec_path = tmp_path / "spec.md"
    spec_sheet.write_spec(s.spec_path, {"project": "a", "mode": "mix"})
    r = executor.run_plan(s, vol_plan())              # P0 is satisfied; P4 needs source, hash, targets, cap
    assert not r.ok and r.error.code == "E_NOT_FOUND" and r.error.detail["completed"] == ["s01"]
    assert r.error.detail["missing"] == ["source", "original_hash", "targets", "iteration_cap"]
    spec_sheet.write_spec(s.spec_path, {"project": "a", "mode": "mix", "source": "x.flp", "original_hash": "sha256:1",
                                        "targets": "t.toml", "iteration_cap": 3})
    s2 = run(run_dir=tmp_path / "r2")
    s2.spec_path = s.spec_path
    assert executor.run_plan(s2, vol_plan()).ok


def test_original_hash_guard(run, tmp_path):
    s = run()
    orig = tmp_path / "orig.flp"
    orig.write_bytes(b"flp data")
    assert record_original(s, orig).ok and check_original(s).ok
    orig.write_bytes(b"changed")
    r = check_original(s)
    assert not r.ok and r.error.code == "E_SANDBOX_VIOLATION"
    assert record_original(s, tmp_path / "missing").error.code == "E_NOT_FOUND"


def test_adhoc_calls_are_ledgered_but_plan_steps_are_not_doubled(run):
    s = run()
    s.registry.call("read_project_summary")
    notes = [e for e in s.ledger.entries() if e["type"] == "note" and e.get("what") == "call"]
    assert len(notes) >= 1 and notes[-1]["module"] == "read_project_summary"
    before = len(s.ledger.entries())
    executor.run_plan(s, {"steps": [vol_plan()["steps"][0]]})
    assert not [e for e in s.ledger.entries()[before:] if e["type"] == "note" and e.get("what") == "call"]


def test_every_exposed_module_is_reachable_and_every_slice_name_exists():

    from coproducer.orchestrator.phases import ALWAYS, ON_DEMAND, SLICES
    from coproducer.registry import Registry
    from coproducer.testrig import MODULES

    reg = Registry(MODULES).load()
    listed = {n for names in SLICES.values() for n in names} | set(ALWAYS) | set(ON_DEMAND)
    exposed = {m.name for m in reg.exposed()}
    assert sorted(exposed - listed) == [], "exposed modules that no phase can reach"
    assert sorted(listed - set(reg.modules)) == [], "slice names that are not modules"
