from __future__ import annotations

import tomllib
from pathlib import Path

from coproducer.datafiles import find_unfilled, missing_keys
from coproducer.result import Result, fail, ok

REQUIRED = {"key": {"tonic": 1, "mode": 1}, "tempo_source_bpm": 1, "tempo_policy": 1, "melody": {"midi": 1, "contour_threshold": 1},
            "harmony": {"chord_loop": 1}, "sections": 1}
POLICIES = ("keep", "genre", "half_time")


def load_invariants_file(path: str) -> Result:
    """Read a project's invariants TOML (what must survive a restyle). Refuses blanks, missing tables and an unknown tempo_policy.

    Errors: E_NOT_FOUND, E_IO, E_ARG.
    """
    f = Path(path)
    if not f.is_file():
        return fail("E_NOT_FOUND", "no invariants file at %s" % path)
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read invariants: %s" % e)
    gone, blanks = missing_keys(data, REQUIRED), find_unfilled(data)
    if gone or blanks or data.get("tempo_policy") not in POLICIES:
        return fail("E_ARG", "invariants are incomplete or invalid", missing=gone, unfilled=blanks, policies=list(POLICIES))
    return ok(data)
