from __future__ import annotations

from coproducer.result import Result, ok


def _dig(node: object, dotted: str) -> object:
    for part in dotted.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def compare_to_reference(report: dict, target: dict) -> Result:
    """Compare a measure report with a target. Each target entry is {value, tolerance}, keyed by dotted path.

    Returns one row per target with the measured value, delta and whether it is within tolerance.
    """
    rows = []
    for path, want in target.items():
        got = _dig(report, path)
        delta = round(got - want["value"], 3) if isinstance(got, (int, float)) else None
        rows.append({"metric": path, "measured": got, "target": want["value"], "tolerance": want["tolerance"],
                     "delta": delta, "within": delta is not None and abs(delta) <= want["tolerance"]})
    return ok({"rows": rows, "all_within": all(r["within"] for r in rows), "missing": [r["metric"] for r in rows if r["delta"] is None]})
