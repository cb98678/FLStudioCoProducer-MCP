from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok

MAX_PATTERN = 999


def list_patterns_summary(limit: int = MAX_PATTERN) -> Result:
    """List the patterns that hold data (numbered from 1) with name and length.

    FL's patternCount counts only non-default patterns and they need not be adjacent (measured 2026-10-20: count 2, data in 3 and 4),
    so the scan walks up from 1 until it has found that many, or reaches limit.
    """
    n = call("op_patterns_pattern_count")
    if not n.ok:
        return n
    rows, i = [], 0
    while len(rows) < n.value and i < limit:
        i += 1
        default = call("op_patterns_is_pattern_default", index=i)
        if not default.ok:
            return default
        if default.value:
            continue
        name = call("op_patterns_get_pattern_name", index=i)
        length = call("op_patterns_get_pattern_length", index=i)
        bad = first_error(name, length)
        if bad:
            return bad
        rows.append({"index": i, "name": name.value, "length": length.value})
    return ok(rows)
