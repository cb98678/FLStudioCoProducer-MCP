"""Plans are data: load, validate against the registry, and resolve $step.path references."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..manifest import AUTONOMY
from ..result import Result, fail, ok
from .paths import walk_path
from .verifiers import VERIFIER_NAMES

PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7")
_REF = re.compile(r"^\$([A-Za-z0-9_]+)\.(.+)$")
_READ_ONLY = ("pure", "reads_fl", "reads_files")


def load_plan(source: Any) -> Result:
    """Load a plan from a dict or a JSON file path."""
    if isinstance(source, dict):
        return ok(source)
    p = Path(source)
    if not p.exists():
        return fail("E_NOT_FOUND", "no plan file at %s" % p.name)
    try:
        return ok(json.loads(p.read_text(encoding="utf-8")))
    except json.JSONDecodeError as e:
        return fail("E_ARG", "plan file is not valid JSON: %s" % e)


def find_refs(obj: Any) -> list[tuple[str, str]]:
    """All (step_id, path) references inside a nested args structure."""
    if isinstance(obj, str):
        m = _REF.match(obj)
        return [(m.group(1), m.group(2))] if m else []
    if isinstance(obj, dict):
        return [r for v in obj.values() for r in find_refs(v)]
    if isinstance(obj, list):
        return [r for v in obj for r in find_refs(v)]
    return []


def resolve_args(obj: Any, results: dict[str, dict]) -> Result:
    """Replace each whole-string $step.path with the value from an earlier step's result."""
    if isinstance(obj, str):
        m = _REF.match(obj)
        if not m:
            return ok(obj)
        if m.group(1) not in results:
            return fail("E_NOT_FOUND", "step %s has no result yet" % m.group(1))
        return walk_path(results[m.group(1)], m.group(2))
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            r = resolve_args(v, results)
            if not r.ok:
                return r
            out[k] = r.value
        return ok(out)
    if isinstance(obj, list):
        items = [resolve_args(v, results) for v in obj]
        bad = next((r for r in items if not r.ok), None)
        return bad or ok([r.value for r in items])
    return ok(obj)


def _step_problems(step: dict, seen: list[str], modules: dict) -> list[str]:
    sid = step.get("id", "?")
    out = []
    if not step.get("id") or step["id"] in seen:
        out.append("%s: id missing or repeated" % sid)
    if step.get("phase") not in PHASES:
        out.append("%s: phase must be one of P0 to P7" % sid)
    mod = modules.get(step.get("module"))
    if mod is None or not mod.expose:
        out.append("%s: module %r is not registered or not exposed" % (sid, step.get("module")))
        return out
    auto = step.get("autonomy", mod.autonomy)
    if auto not in AUTONOMY or auto == "A3":
        out.append("%s: autonomy %r is not allowed in a plan (A3 is human only)" % (sid, auto))
    elif AUTONOMY.index(auto) < AUTONOMY.index(mod.autonomy):
        out.append("%s: autonomy %s is looser than the module's %s" % (sid, auto, mod.autonomy))
    ver = step.get("verifier")
    if ver not in VERIFIER_NAMES:
        out.append("%s: verifier %r is missing or unknown" % (sid, ver))
    elif ver == "none" and mod.side_effect not in _READ_ONLY:
        out.append("%s: a writing module needs a real verifier" % sid)
    for ref, _ in find_refs([step.get("args", {}), step.get("verify", {})]):
        if ref not in seen:
            out.append("%s: reference to %s which is not an earlier step" % (sid, ref))
    return out


def validate_plan(plan: dict, modules: dict) -> Result:
    """Check a plan against the registry's modules; returns every problem at once."""
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return fail("E_ARG", "a plan needs a non-empty steps list")
    problems, seen = [], []
    for step in steps:
        problems += _step_problems(step, seen, modules)
        seen.append(step.get("id", "?"))
    if problems:
        return fail("E_ARG", "plan has %d problem(s)" % len(problems), problems=problems)
    return ok({"steps": len(steps)})
