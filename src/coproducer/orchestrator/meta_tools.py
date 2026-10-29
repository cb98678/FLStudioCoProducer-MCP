"""Orchestrator meta tools: the agent's handles on the run itself (plan, spec, phase, questions, ledger, halt)."""
from __future__ import annotations

import datetime
import json
from typing import Any, Callable

from ..result import Result, fail, ok
from . import executor, phases, spec_sheet
from .plan import validate_plan
from .session import Session, request_halt, save_state


def _obj(props: dict | None = None, required: list | None = None) -> dict:
    return {"type": "object", "properties": props or {}, "required": required or [], "additionalProperties": False}


def plan_get(s: Session) -> Result:
    done = s.ledger.done_steps()
    steps = [{"id": st["id"], "phase": st["phase"], "module": st["module"], "done": st["id"] in done}
             for st in (s.plan or {}).get("steps", [])]
    return ok({"plan_id": (s.plan or {}).get("plan_id"), "steps": steps})


def plan_set(s: Session, plan: dict) -> Result:
    """Store a new plan after validating it against the registry."""
    checked = validate_plan(plan, s.registry.modules)
    if not checked.ok:
        return checked
    s.plan = plan
    (s.run_dir / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8", newline="\n")
    s.ledger.append("plan_set", plan_id=plan.get("plan_id"), steps=len(plan["steps"]))
    save_state(s)
    return checked


def plan_update(s: Session, steps: list) -> Result:
    """Replace every step that has not finished. Finished steps stay as they are."""
    if s.plan is None:
        return fail("E_NOT_FOUND", "there is no plan to update; use plan_set")
    done = s.ledger.done_steps()
    kept = [st for st in s.plan["steps"] if st["id"] in done]
    return plan_set(s, {**s.plan, "steps": kept + steps})


def plan_run(s: Session) -> Result:
    """Run the stored plan from the first unfinished step."""
    if s.plan is None:
        return fail("E_NOT_FOUND", "there is no plan; use plan_set")
    out = executor.run_plan(s, s.plan)
    save_state(s)
    return out


def spec_get(s: Session) -> Result:
    got = spec_sheet.read_spec(s.spec_path) if s.spec_path else fail("E_NOT_FOUND", "no spec sheet is set for this run")
    return got if not got.ok else ok(spec_sheet.digest(got.value["header"], got.value["body"]))


def record_decision(s: Session, text: str, reason: str) -> Result:
    if not s.spec_path:
        return fail("E_NOT_FOUND", "no spec sheet is set for this run")
    done = spec_sheet.add_decision(s.spec_path, text, reason, datetime.date.today().isoformat())
    if done.ok:
        s.ledger.append("decision", text=text, reason=reason)
    return done


def ask_human(s: Session, question: str, options: list) -> Result:
    if s.ask_budget <= 0:
        return fail("E_PENDING_HUMAN", "the question budget is used up; proceed on the recommended option and log it as an assumption",
                    question=question, budget_exhausted=True)
    s.ask_budget -= 1
    s.ledger.append("ask", question=question, options=options)
    got = s.collab.ask(question, options)
    if got.ok:
        s.ledger.append("answer", question=question, choice=got.value["choice"])
    save_state(s)
    return got


def phase_advance(s: Session, to: str) -> Result:
    out = phases.advance_phase(s, to)
    save_state(s)
    return out


def ledger_tail(s: Session, n: int = 10) -> Result:
    return ok(s.ledger.tail(n))


def halt_run(s: Session, reason: str = "halted by the agent") -> Result:
    request_halt(s, reason)
    return ok(True)


def request_tool(s: Session, name: str, reason: str) -> Result:
    """Ask for a module outside the current phase slice; the addition is logged."""
    mod = s.registry.modules.get(name)
    if mod is None or not mod.expose:
        return fail("E_NOT_FOUND", "no exposed module named %r" % name, nearest=s.registry.nearest(name))
    s.extra_tools.add(name)
    s.ledger.append("note", what="tool_added", module=name, reason=reason, phase=s.phase)
    save_state(s)
    return ok(phases.slice_for(s))


# The guides a chat reads before working: skills (SKILL.md and their references), docs and the style packs. Read only; nothing else is served.
GUIDE_DIRS = ("skills", "docs", "styles", "recipes")
GUIDE_TYPES = (".md", ".json", ".toml")


def _home(s: Session):
    return s.registry.root.resolve().parent


def _front(text: str) -> dict:
    """name and description from a SKILL.md front matter block."""
    out: dict = {}
    if text.startswith("---"):
        for line in text.split("---", 2)[1].splitlines():
            k, _, v = line.partition(":")
            if k.strip() in ("name", "description"):
                out[k.strip()] = v.strip()
    return out


def list_skills(s: Session) -> Result:
    """Every skill with its description and reference files, plus the docs. Start here, then read co-producer-protocol."""
    home = _home(s)
    skills = []
    for md in sorted((home / "skills").glob("*/SKILL.md")):
        refs = sorted(p.relative_to(md.parent).as_posix() for p in md.parent.rglob("*.md") if p != md)
        skills.append({**_front(md.read_text(encoding="utf-8")), "folder": md.parent.name, "references": refs})
    docs = sorted(p.relative_to(home).as_posix() for p in (home / "docs").glob("*.md")) if (home / "docs").is_dir() else []
    styles = sorted(p.stem for p in (home / "styles").glob("*.json")) if (home / "styles").is_dir() else []
    return ok({"skills": skills, "docs": docs, "styles": styles,
               "start": "read_skill co-producer-protocol, then the skill for the task (remix-from-stems for a remix) and its references"})


def read_skill(s: Session, name: str) -> Result:
    """One guide as text: a skill name ('remix-from-stems'), a skill file ('remix-from-stems/references/creative-brief.md'),
    a doc ('docs/HANDOFF.md') or a style pack ('styles/house.json'). Paths stay inside skills, docs, styles and recipes."""
    home = _home(s)
    rel = name.strip().replace("\\", "/").strip("/")
    first = rel.split("/", 1)[0]
    path = home / rel if first in GUIDE_DIRS else home / "skills" / rel
    if path.is_dir():
        path = path / "SKILL.md"
    try:
        path = path.resolve()
        allowed = any(path.is_relative_to((home / d).resolve()) for d in GUIDE_DIRS)
    except (OSError, ValueError):
        allowed = False
    if not allowed or path.suffix not in GUIDE_TYPES:
        return fail("E_ARG", "only skills, docs, styles and recipes files (.md, .json, .toml) can be read", name=name)
    if not path.is_file():
        near = [x["folder"] for x in list_skills(s).value["skills"] if first.lower() in x["folder"]]
        return fail("E_NOT_FOUND", "no guide at %s" % rel, nearest=near)
    return ok({"path": path.relative_to(home.resolve()).as_posix(), "text": path.read_text(encoding="utf-8")})


def run_status(s: Session) -> Result:
    return ok({"phase": s.phase, "iteration": s.iteration, "questions_left": s.ask_budget,
               "actions_used": s.actions, "action_budget": s.action_budget,
               "halted": (s.run_dir / "HALT").exists() or s.halt.is_set(), "tools": phases.slice_for(s),
               "ledger_entries": s.ledger.seq})


# name -> (summary, schema, function)
META: dict[str, tuple[str, dict, Callable[..., Result]]] = {
    "plan_get": ("Return the current plan with each step's status.", _obj(), plan_get),
    "plan_set": ("Store a plan (steps of module calls with verifiers) after validating it.", _obj({"plan": {"type": "object"}}, ["plan"]), plan_set),
    "plan_update": ("Replace every unfinished step with new steps.", _obj({"steps": {"type": "array", "items": {"type": "object"}}}, ["steps"]), plan_update),
    "plan_run": ("Run the stored plan from the first unfinished step; stops at the first failure.", _obj(), plan_run),
    "spec_get": ("Return the spec sheet digest for this project.", _obj(), spec_get),
    "record_decision": ("Add a decision and its reason to the spec sheet.", _obj({"text": {"type": "string", "minLength": 1}, "reason": {"type": "string", "minLength": 1}}, ["text", "reason"]), record_decision),
    "ask_human": ("Ask the human a question with 2 to 4 options, recommended option first.", _obj({"question": {"type": "string", "minLength": 1}, "options": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4}}, ["question", "options"]), ask_human),
    "phase_advance": ("Move to another phase after its exit check passes.", _obj({"to": {"type": "string", "enum": list(phases.PHASES)}}, ["to"]), phase_advance),
    "ledger_tail": ("Return the last N ledger entries.", _obj({"n": {"type": "integer", "minimum": 1, "maximum": 200}}), ledger_tail),
    "halt_run": ("Stop the run cleanly; every server refuses further steps.", _obj({"reason": {"type": "string"}}), halt_run),
    "request_tool": ("Ask for one module outside the current phase slice, with a reason.", _obj({"name": {"type": "string", "minLength": 1}, "reason": {"type": "string", "minLength": 1}}, ["name", "reason"]), request_tool),
    "run_status": ("Return phase, budgets, halt flag and the tool slice.", _obj(), run_status),
    "list_skills": ("List the co-producer's skills, docs and style packs. Call first in a new chat, then read_skill co-producer-protocol.", _obj(), list_skills),
    "read_skill": ("Read one skill, skill reference, doc or style pack as text (a skill name or a path such as remix-from-stems/references/creative-brief.md).",
                   _obj({"name": {"type": "string", "minLength": 1}}, ["name"]), read_skill),
}


def call_meta(s: Session, name: str, args: dict[str, Any]) -> Result:
    """Validate and run one meta tool."""
    from ..schema import validate_args
    entry = META.get(name)
    if entry is None:
        return fail("E_NOT_FOUND", "no meta tool named %r" % name)
    chk = validate_args(entry[1], args)
    if not chk.ok:
        return chk
    try:
        return entry[2](s, **args)
    except Exception as e:  # noqa: BLE001 - a meta tool must return a Result
        return fail("E_INTERNAL", "%s raised %s: %s" % (name, type(e).__name__, e))
