"""coproducer run and resume: execute a plan against FL, asking the human in the terminal (or leaving questions in a file)."""
from __future__ import annotations

import json
from pathlib import Path

from ..orchestrator.collab import CallbackCollab, PendingCollab
from ..orchestrator.executor import run_plan
from ..orchestrator.session import save_state
from ..servers.common import attach_bridge, make_session


def terminal_collab() -> CallbackCollab:
    def ask(question: str, options: list) -> str:
        print("\n" + question)
        for i, o in enumerate(options, 1):
            print("  %d. %s" % (i, o))
        raw = input("choose a number or type an answer: ").strip()
        return options[int(raw) - 1] if raw.isdigit() and 0 < int(raw) <= len(options) else raw

    def approve(what: str, detail: dict) -> bool:
        print("\nApproval needed: %s\n%s" % (what, json.dumps(detail, indent=2)[:1500]))
        return input("type yes to approve: ").strip().lower() == "yes"
    return CallbackCollab(ask, approve)


def load_plan_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def execute(home: Path, run_id: str, plan: dict | None, spec: Path | None, unattended: bool, ceiling: str, connect: bool = True) -> tuple:
    """Build the session, connect to FL, run the plan. Returns (exit_code, text)."""
    s = make_session(home, run_id, "fl-bridge", ceiling)
    if unattended:
        s.collab = PendingCollab(s.run_dir / "pending_decisions.json")
    else:
        s.collab = terminal_collab()
    if connect:
        warn = attach_bridge(s, "coproducer-in", "coproducer-out")
        if warn:
            return 3, "FL is not connected: %s" % warn
    if spec:
        s.spec_path = spec
    plan = plan or s.plan
    if not plan:
        return 2, "this run has no saved plan; pass a plan file"
    res = run_plan(s, plan)
    save_state(s)
    if res.ok:
        return 0, "finished: %s" % json.dumps(res.value)
    if res.error.code == "E_PENDING_HUMAN":
        return 4, "waiting for you. Answer the questions in %s then run: coproducer resume %s" % (s.run_dir / "pending_decisions.json", run_id)
    if res.error.detail.get("status") == "waiting_for_fl":
        return 5, "paused, waiting for FL Studio. %s" % res.error.message.replace("<run id>", run_id)
    return 1, "stopped: %s %s" % (res.error.code, res.error.message)
