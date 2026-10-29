"""One run: the registry, ledger, collaborator, snapshots, halt flag and budgets, kept together."""
from __future__ import annotations

import hashlib
import json
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..registry import Registry, call_depth
from ..result import Result, fail, ok
from .ledger import Ledger


@dataclass
class Session:
    registry: Registry
    ledger: Ledger
    collab: Any
    run_dir: Path
    spec_path: Path | None = None
    phase: str = "P0"
    entered: str | None = None
    plan: dict | None = None
    results: dict = field(default_factory=dict)
    snapshots: dict = field(default_factory=dict)
    halt: threading.Event = field(default_factory=threading.Event)
    actions: int = 0
    action_budget: int = 200
    ask_budget: int = 12
    approved_now: str | frozenset | None = None  # the A1 module (or set of them) approved for the call in progress
    in_plan_step: bool = False
    original: dict | None = None
    waiting: str | None = None
    extra_tools: set = field(default_factory=set)
    iteration: int = 0

    @contextmanager
    def quiet(self):
        """Calls made inside are the executor's own and are not logged as ad hoc calls."""
        before, self.in_plan_step = self.in_plan_step, True
        try:
            yield
        finally:
            self.in_plan_step = before


def hash_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def record_original(s: Session, path: Path | str) -> Result:
    """Remember the hash of the original project so P7 can prove it was never written."""
    p = Path(path)
    if not p.is_file():
        return fail("E_NOT_FOUND", "no original project file at %s" % p.name)
    s.original = {"path": str(p), "hash": hash_file(p)}
    s.ledger.append("note", what="original_recorded", project_hash=s.original["hash"])
    return ok(s.original["hash"])


def check_original(s: Session) -> Result:
    if not s.original:
        return fail("E_NOT_FOUND", "no original hash recorded")
    now = hash_file(s.original["path"]) if Path(s.original["path"]).is_file() else "missing"
    if now != s.original["hash"]:
        return fail("E_SANDBOX_VIOLATION", "the original project changed", expected=s.original["hash"], found=now)
    return ok(True)


def save_snapshot(s: Session, snap_id: str, snap: dict) -> None:
    s.snapshots[snap_id] = snap
    d = s.run_dir / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    (d / (snap_id + ".json")).write_text(json.dumps(snap), encoding="utf-8", newline="\n")


STATE_KEYS = ("phase", "entered", "plan", "iteration", "actions", "original", "ask_budget", "action_budget")


def save_state(s: Session) -> None:
    """Persist what other server processes of the same run need: phase, plan, budgets, slice additions."""
    data = {k: getattr(s, k) for k in STATE_KEYS}
    data["extra_tools"] = sorted(s.extra_tools)
    data["spec_path"] = str(s.spec_path) if s.spec_path else None
    tmp = s.run_dir / "state.json.tmp"
    tmp.write_text(json.dumps(data), encoding="utf-8", newline="\n")
    tmp.replace(s.run_dir / "state.json")


def load_state(s: Session) -> None:
    f = s.run_dir / "state.json"
    if not f.exists():
        return
    data = json.loads(f.read_text(encoding="utf-8"))
    for k in STATE_KEYS:
        if k in data:
            setattr(s, k, data[k])
    s.extra_tools = set(data.get("extra_tools", []))
    s.spec_path = Path(data["spec_path"]) if data.get("spec_path") else None


def halted(s: Session) -> bool:
    """True when this process, any other process of the run, or the global halt key asked to stop (the HALT files)."""
    return s.halt.is_set() or (s.run_dir / "HALT").exists() or (s.run_dir.parent / "HALT").exists()


def request_halt(s: Session, reason: str) -> None:
    s.halt.set()
    s.run_dir.mkdir(parents=True, exist_ok=True)
    (s.run_dir / "HALT").write_text(reason, encoding="utf-8")
    s.ledger.append("halt", reason=reason)


def new_session(modules_root: Path | str, run_dir: Path | str, collab: Any, ceiling: str = "A2",
                fl_proxy: Any = None, lint: bool = True) -> Session:
    """Build a registry wired to the ledger and the approval flow, and return the session around it."""
    run_dir = Path(run_dir)
    ledger = Ledger(run_dir / "ledger.jsonl")
    holder: dict = {}

    def approver(name: str, kwargs: dict) -> bool:
        now = holder["s"].approved_now
        return now == name or (isinstance(now, (set, frozenset, tuple)) and name in now)

    def observer(name: str, kwargs: dict, res: Result, secs: float) -> None:
        s = holder["s"]
        if not s.in_plan_step and call_depth() == 0:
            ledger.append("note", what="call", module=name, args=kwargs, ok=res.ok, secs=round(secs, 3),
                          code=None if res.ok else res.error.code, verified=res.meta.get("verified"))

    reg = Registry(modules_root, ceiling=ceiling, approver=approver, observer=observer, fl_proxy=fl_proxy)
    reg.load(lint=lint)
    s = Session(registry=reg, ledger=ledger, collab=collab, run_dir=run_dir)
    holder["s"] = s
    load_state(s)
    return s
