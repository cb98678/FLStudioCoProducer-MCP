from __future__ import annotations

import tomllib
from pathlib import Path

from coproducer.datafiles import find_unfilled, missing_keys
from coproducer.result import Result, fail, ok

REQUIRED = {"meta": {"name": 1}, "tempo": {"range_bpm": 1, "feel": 1}, "structure": {"sections": 1}, "drums": {"kick_pattern_steps": 1},
            "bass": {"patch_family": 1, "register_hz": 1}, "mix": {"targets": 1, "bus_layout": 1}}


def load_genre_profile(path: str, allow_blanks: bool = False) -> Result:
    """Read a genre profile TOML and check it has every required table. Blanks (FILL) are refused unless allow_blanks.

    Errors: E_NOT_FOUND, E_IO, E_ARG listing missing keys or blanks.
    """
    f = Path(path)
    if not f.is_file():
        return fail("E_NOT_FOUND", "no genre profile at %s" % path)
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read the profile: %s" % e)
    gone, blanks = missing_keys(data, REQUIRED), find_unfilled(data)
    if gone or (blanks and not allow_blanks):
        return fail("E_ARG", "the profile is incomplete", missing=gone, unfilled=blanks)
    return ok({"profile": data, "unfilled": blanks})
