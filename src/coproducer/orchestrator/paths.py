"""Dotted-path lookup shared by plan references and verifiers."""
from __future__ import annotations

from typing import Any

from ..result import Result, fail, ok


def walk_path(value: Any, path: str) -> Result:
    """Follow a dotted path through dicts and lists."""
    cur = value
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return fail("E_NOT_FOUND", "path %r not found at %r" % (path, part))
    return ok(cur)
