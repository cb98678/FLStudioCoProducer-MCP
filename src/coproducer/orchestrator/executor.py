"""Run a validated plan: gate, call, record, verify, and stop safely when anything goes wrong."""
from __future__ import annotations

from ..result import Result, fail, ok
from . import spec_sheet
from .plan import resolve_args, validate_plan
from .session import Session, check_original, halted, request_halt, save_snapshot
from .verifiers import VerifyCtx, run_verifier

_READ = ("pure", "reads_fl", "reads_files")
_FL_CALLS = ("reads_fl", "writes_fl_sandbox")
WAIT_HELP = ("FL Studio is not answering. Start FL Studio, open the sandbox project, check that the Coproducer script is selected "
             "in Options > MIDI settings (View > Script output shows 'Coproducer bridge ready'), then run: coproducer resume <run id>")
MAX_READ_RETRIES = 2


def _gate(s: Session, step: dict) -> Result:
    """Halt flag, action budget and A1 approval, checked before every step."""
    mod = s.registry.modules[step["module"]]
    if halted(s):
        return fail("E_HALTED", "the run was halted")
    if mod.side_effect == "gui":
        s.actions += 1
        if s.actions > s.action_budget:
            request_halt(s, "GUI action budget used up")
            return fail("E_HALTED", "the GUI action budget (%d) is used up" % s.action_budget)
    level = step.get("autonomy", mod.autonomy)
    if level == "A1":
        ok_ = s.collab.approve("run %s (%s)" % (step["module"], step["id"]), {"args": step.get("args", {})})
        s.ledger.append("answer", step_id=step["id"], approved=ok_.ok)
        if not ok_.ok:
            return ok_
        s.approved_now = step["module"]
    return ok(True)


def _call_with_retry(s: Session, step: dict, args: dict) -> Result:
    mod = s.registry.modules[step["module"]]
    tries = 1 + (MAX_READ_RETRIES if mod.side_effect in _READ else 0)
    res = fail("E_INTERNAL", "not run")
    for _ in range(tries):
        res = s.registry.call(step["module"], **args)
        if res.ok or not res.error.retryable:
            break
    return res


def _fl_stopped_answering(s: Session, step: dict, res: Result) -> bool:
    """True when an FL call timed out and FL does not answer a ping either. A slow single call is not this."""
    if res.error is None or res.error.code != "E_TIMEOUT" or s.registry.modules[step["module"]].side_effect not in _FL_CALLS:
        return False
    if "ping_fl" not in s.registry.modules:
        return False
    with s.quiet():
        return not s.registry.call("ping_fl").ok


def _waiting_result(step_id: str, module: str, known: bool) -> Result:
    note = "" if known else " The step changes the project, so it may or may not have happened."
    return fail("E_TIMEOUT", "FL Studio stopped answering at step %s; the run is paused in waiting_for_fl.%s %s" % (step_id, note, WAIT_HELP),
                retryable=True, status="waiting_for_fl", outcome_known=known, step=step_id, module=module)


def _pause_for_fl(s: Session, step: dict) -> Result:
    """Record that the run is waiting for FL. No rollback is offered: FL cannot be reached to roll anything back."""
    mod = s.registry.modules[step["module"]]
    known = mod.side_effect == "reads_fl" or bool(mod.manifest["policy"].get("idempotent", False))
    s.waiting = "waiting_for_fl"
    s.ledger.append("waiting_for_fl", step_id=step["id"], module=step["module"], outcome_known=known)
    return _waiting_result(step["id"], step["module"], known)


def _resume_after_wait(s: Session) -> Result:
    """A run that paused for FL starts again only when FL answers. A write whose outcome is unknown needs the human's word."""
    last = next((e for e in reversed(s.ledger.entries()) if e["type"] in ("waiting_for_fl", "resume_after_wait")), None)
    if not last or last["type"] != "waiting_for_fl":
        return ok(False)
    with s.quiet():
        alive = s.registry.call("ping_fl") if "ping_fl" in s.registry.modules else ok(True)
    if not alive.ok:
        return _waiting_result(last["step_id"], last["module"], last["outcome_known"])
    if not last["outcome_known"]:
        question = ("Step %s (%s) changes the project and FL stopped answering while it ran, so it may or may not have happened. "
                    "Look in FL. Run it again?" % (last["step_id"], last["module"]))
        asked = s.collab.ask(question, ["run it again", "stop here"])
        s.ledger.append("ask", step_id=last["step_id"], options=["run it again", "stop here"], answered=asked.ok)
        if not asked.ok:
            return asked
        if asked.value["choice"] != "run it again":
            return fail("E_HALTED", "stopped at your choice before repeating step %s" % last["step_id"], stopped_at=last["step_id"])
    s.waiting = None
    s.ledger.append("resume_after_wait", step_id=last["step_id"])
    return ok(True)


def _snapshot(s: Session, snap_id: str, why: str) -> None:
    if "snapshot_state" not in s.registry.modules:
        return
    with s.quiet():
        got = s.registry.call("snapshot_state")
    if got.ok:
        save_snapshot(s, snap_id, got.value)
        s.ledger.append("snapshot", snapshot_id=snap_id, why=why)


def _verify(s: Session, step: dict, res: Result) -> Result:
    resolved = resolve_args(step.get("verify", {}), s.results)
    if not resolved.ok:
        return resolved
    ctx = VerifyCtx(call=s.registry.call, collab=s.collab, original_ok=lambda: check_original(s))
    with s.quiet():
        verdict = run_verifier(step, res, resolved.value, ctx)
    s.ledger.append("verify", step_id=step["id"], verifier=step["verifier"], passed=verdict.ok,
                    detail=None if verdict.ok else verdict.error.message)
    return verdict


def _on_failure(s: Session, step: dict, why: Result) -> Result:
    """Offer a rollback to the last snapshot, then stop. Never repeats a write on its own."""
    snap_id = next(reversed(s.snapshots), None)
    options = ["stop here"] + (["roll back to snapshot %s" % snap_id] if snap_id else [])
    asked = s.collab.ask("Step %s failed: %s. What now?" % (step["id"], why.error.message), options)
    s.ledger.append("ask", step_id=step["id"], options=options, answered=asked.ok)
    if asked.ok and asked.value["choice"].startswith("roll back") and snap_id:
        with s.quiet():
            rb = s.registry.call("rollback_to", snapshot=s.snapshots[snap_id])
        s.ledger.append("rollback", snapshot_id=snap_id, ok=rb.ok, detail=None if rb.ok else rb.error.message)
    return why


def run_step(s: Session, step: dict) -> Result:
    """Run one step end to end. ok means the call succeeded and its verifier passed."""
    gate = _gate(s, step)
    if not gate.ok:
        return gate
    args = resolve_args(step.get("args", {}), s.results)
    if not args.ok:
        return args
    if step.get("risky"):
        _snapshot(s, "before_" + step["id"], "risky step")
    s.ledger.append("step_start", step_id=step["id"], module=step["module"], args=args.value)
    try:
        with s.quiet():
            res = _call_with_retry(s, step, args.value)
    finally:
        s.approved_now = None
    s.ledger.append("step_result", step_id=step["id"], ok=res.ok, value=res.value, meta=res.meta,
                    code=None if res.ok else res.error.code, message=None if res.ok else res.error.message,
                    verified=res.meta.get("verified"), project_hash=s.original["hash"] if s.original else None)
    if not res.ok:
        return res
    s.results[step["id"]] = res.to_dict()
    verdict = _verify(s, step, res)
    return ok(res.value, **res.meta) if verdict.ok else verdict


def _enter_phase(s: Session, phase: str) -> Result:
    if s.spec_path:
        got = spec_sheet.read_spec(s.spec_path)
        gaps = spec_sheet.missing_fields(got.value["header"], phase) if got.ok else ["spec sheet"]
        if gaps:
            return fail("E_NOT_FOUND", "the spec sheet is missing %s for %s" % (", ".join(gaps), phase), missing=gaps)
    s.phase = s.entered = phase
    s.ledger.append("phase_enter", phase=phase)
    _snapshot(s, "start_" + phase, "phase entry")
    return ok(phase)


def _load_done(s: Session) -> list[str]:
    """Reload results of steps already finished and verified in this run's ledger (resume)."""
    for sid, entry in s.ledger.done_steps().items():
        s.results[sid] = {"ok": True, "value": entry.get("value"), "error": None, "meta": entry.get("meta") or {}}
    return list(s.results)


def run_plan(s: Session, plan: dict) -> Result:
    """Validate and run a plan from the first step without a verified result."""
    checked = validate_plan(plan, s.registry.modules)
    if not checked.ok:
        return checked
    s.plan = plan
    waited = _resume_after_wait(s)
    if not waited.ok:
        return waited
    s.ledger.append("plan_set", plan_id=plan.get("plan_id"), steps=len(plan["steps"]))
    skipped, completed = _load_done(s), []
    for step in plan["steps"]:
        if step["id"] in skipped:
            continue
        entered = _enter_phase(s, step["phase"]) if step["phase"] != s.entered else ok(s.entered)
        if not entered.ok:
            return _stopped(entered, step, completed, skipped)
        out = run_step(s, step)
        if not out.ok:
            if _fl_stopped_answering(s, step, out):
                return _stopped(_pause_for_fl(s, step), step, completed, skipped)
            return _stopped(_on_failure(s, step, out), step, completed, skipped)
        completed.append(step["id"])
    return ok({"completed": completed, "resumed": skipped})


def _stopped(why: Result, step: dict, completed: list, resumed: list) -> Result:
    code = why.error.code
    return fail(code, why.error.message, why.error.retryable, stopped_at=step["id"], completed=completed,
                resumed=resumed, **{k: v for k, v in why.error.detail.items() if k not in ("stopped_at", "completed", "resumed")})
