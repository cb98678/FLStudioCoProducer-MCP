from __future__ import annotations

from coproducer.result import Result, ok


def _flat(node: object, prefix: str, out: dict) -> dict:
    if isinstance(node, dict):
        for k, v in node.items():
            _flat(v, prefix + "." + str(k) if prefix else str(k), out)
    else:
        out[prefix] = node
    return out


def diff_state_snapshots(before: dict, after: dict) -> Result:
    """Compare two state snapshots and list every value that changed, appeared or disappeared.

    Numbers within 1e-6 count as equal. Each change is {path, before, after}, sorted by path.
    """
    a, b = _flat(before, "", {}), _flat(after, "", {})
    changes = []
    for path in sorted(set(a) | set(b)):
        x, y = a.get(path), b.get(path)
        same = abs(x - y) < 1e-6 if isinstance(x, float) and isinstance(y, (int, float)) else x == y
        if path not in a or path not in b or not same:
            changes.append({"path": path, "before": x, "after": y})
    return ok(changes)
