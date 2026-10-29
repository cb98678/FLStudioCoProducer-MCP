from __future__ import annotations

from coproducer.result import Result, fail, ok


def _dig(d, dotted: str):
    for part in dotted.split("."):
        d = d.get(part) if isinstance(d, dict) else None
    return d


def check_report_limits(report: dict, limits: list) -> Result:
    """Compare a measure report with limits ({path, min?, max?, label}). Returns one row per limit and the list that failed.

    A limit whose metric is missing or not a number counts as failed.
    """
    if not limits:
        return fail("E_ARG", "no limits to check")
    rows = []
    for lim in limits:
        got = _dig(report, lim["path"])
        num = isinstance(got, (int, float)) and not isinstance(got, bool)
        inside = num and lim.get("min", float("-inf")) <= got <= lim.get("max", float("inf"))
        rows.append({"label": lim.get("label", lim["path"]), "measured": got if num else None, "min": lim.get("min"), "max": lim.get("max"),
                     "within": bool(inside), "delta": None if not num else round(got - (lim["max"] if got > lim.get("max", got) else lim["min"] if got < lim.get("min", got) else got), 3)})
    return ok({"rows": rows, "all_within": all(r["within"] for r in rows), "failing": [r["label"] for r in rows if not r["within"]]})
