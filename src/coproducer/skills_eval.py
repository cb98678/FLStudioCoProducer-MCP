"""Check skill eval assertions against a run transcript. Structural assertions are decided here; judgment calls are returned as needs_review.

Transcript: {"calls": [{"module", "args", "ok", "verified"}], "asks": [{"question", "options"}], "text": str,
             "skills_loaded": [str], "plan": {"steps": [...]}, "files": [str], "gate_passed": bool, "pending": bool, "halted": bool}
Context: {"writes": set of module names that change state}
"""
from __future__ import annotations

JUDGED = ("text_has_numbers_with_units", "no_invented_target", "single_change", "recommendation_first", "no_guess",
          "only_flagged_lines_changed", "within_delta_cap")


def _calls(t: dict, module: str) -> list:
    return [c for c in t.get("calls", []) if c["module"] == module]


def _index(t: dict, module: str) -> int | None:
    return next((i for i, c in enumerate(t.get("calls", [])) if c["module"] == module), None)


def _matches(call: dict, want: dict) -> bool:
    return all(call.get("args", {}).get(k) == v for k, v in want.items())


def _writes(t: dict, ctx: dict) -> list:
    return [c for c in t.get("calls", []) if c["module"] in ctx.get("writes", set())]


def _called_before(a: dict, t: dict, ctx: dict) -> bool:
    i, j = _index(t, a["a"]), _index(t, a["b"])
    return i is not None and (j is None or i < j)


def _same_call(a: dict, t: dict, ctx: dict) -> bool:
    seen = [repr(sorted(c.get("args", {}).items())) for c in _calls(t, a["module"])]
    return len(seen) == len(set(seen))


def _no_calls_after_ask(a: dict, t: dict, ctx: dict) -> bool:
    return bool(t.get("asks")) and t.get("calls_after_ask", 0) == 0


def _options_between(a: dict, t: dict, ctx: dict) -> bool:
    lo, hi = a["options_between"]
    return any(lo <= len(q.get("options", [])) <= hi for q in t.get("asks", []))


def _plan_review(a: dict, t: dict, ctx: dict) -> bool:
    steps = t.get("plan", {}).get("steps", [])
    return any(s.get("verifier") == "human_review" or s["module"] == "ask_human" for s in steps)


CHECKS = {
    "tool_called": lambda a, t, c: any(_matches(x, a.get("args_match", {})) for x in _calls(t, a["module"])),
    "tool_not_called": lambda a, t, c: not any(_matches(x, a.get("args_match", {})) for x in _calls(t, a["module"])),
    "called_before": _called_before,
    "tool_called_after_change": lambda a, t, c: any(i > min([k for k, x in enumerate(t["calls"]) if x["module"] in c.get("writes", set())] or [10**9])
                                                    for i, x in enumerate(t.get("calls", [])) if x["module"] == a["module"]),
    "same_call_not_repeated": _same_call,
    "all_writes_verified": lambda a, t, c: all(x.get("verified") is True for x in _writes(t, c)),
    "result_verified": lambda a, t, c: all(x.get("verified") is True for x in _calls(t, a["module"])) and bool(_calls(t, a["module"])),
    "no_write_calls": lambda a, t, c: not _writes(t, c),
    "all_writes_have_verifier": lambda a, t, c: all(s.get("verifier", "none") != "none" for s in t.get("plan", {}).get("steps", []) if s["module"] in c.get("writes", set())),
    "no_a3": lambda a, t, c: not any(s.get("autonomy") == "A3" for s in t.get("plan", {}).get("steps", [])),
    "plan_has_human_review": _plan_review,
    "asked_human": lambda a, t, c: bool(t.get("asks")) and (not a.get("about") or any(a["about"] in q.get("question", "").lower() for q in t["asks"])),
    "options_between": _options_between,
    "no_calls_after_ask": _no_calls_after_ask,
    "pending_decision_written": lambda a, t, c: bool(t.get("pending")),
    "stopped": lambda a, t, c: bool(t.get("halted") or t.get("pending")),
    "text_mentions": lambda a, t, c: a["text"].lower() in t.get("text", "").lower(),
    "text_absent": lambda a, t, c: a["text"] not in t.get("text", ""),
    "skill_loaded": lambda a, t, c: a["skill"] in t.get("skills_loaded", []),
    "skill_not_loaded": lambda a, t, c: not t.get("skills_loaded"),
    "files_returned": lambda a, t, c: sorted(t.get("files", [])) == sorted(a["files"]),
    "gate_passes": lambda a, t, c: bool(t.get("gate_passed")),
}


def check_assertion(a: dict, t: dict, ctx: dict) -> str:
    """'pass', 'fail', 'needs_review' or 'unknown' for one assertion."""
    if a["type"] == "any_of":
        got = {check_assertion(x, t, ctx) for x in a["of"]}
        return "pass" if "pass" in got else ("needs_review" if "needs_review" in got else "fail")
    if a["type"] in JUDGED:
        return "needs_review"
    fn = CHECKS.get(a["type"])
    return "unknown" if fn is None else ("pass" if fn(a, t, ctx) else "fail")


def check_eval(ev: dict, transcript: dict, ctx: dict) -> dict:
    """Run every assertion of one eval. Also checks the skill triggered (or stayed quiet) as the eval says."""
    rows = [(a["type"], check_assertion(a, transcript, ctx)) for a in ev["assertions"]]
    return {"id": ev["id"], "rows": rows, "passed": all(r == "pass" for _, r in rows), "needs_review": [t for t, r in rows if r == "needs_review"],
            "failed": [t for t, r in rows if r in ("fail", "unknown")]}
