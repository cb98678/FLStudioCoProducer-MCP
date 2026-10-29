"""Helpers for the user-owned data files (targets, genre profiles, invariants). They are TOML; blanks are written as "FILL..."."""
from __future__ import annotations


def find_unfilled(obj, prefix: str = "") -> list:
    """Dotted paths of every value that is still a FILL placeholder."""
    if isinstance(obj, dict):
        return [p for k, v in obj.items() for p in find_unfilled(v, prefix + k + ".")]
    if isinstance(obj, list):
        return [p for i, v in enumerate(obj) for p in find_unfilled(v, "%s%d." % (prefix, i))]
    return [prefix.rstrip(".")] if isinstance(obj, str) and obj.startswith("FILL") else []


def missing_keys(obj: dict, required: dict, prefix: str = "") -> list:
    """Dotted paths named in `required` (nested dict, leaf value ignored) that are absent from obj."""
    out = []
    for k, sub in required.items():
        if not isinstance(obj, dict) or k not in obj:
            out.append(prefix + k)
        elif isinstance(sub, dict):
            out += missing_keys(obj[k], sub, prefix + k + ".")
    return out
