"""Read-only probe of how FL numbers patterns and playlist tracks, using only ops the FL side already has.

Answers: does patternCount count from 1 and stay adjacent, which index is the first real pattern, and how many playlist tracks exist.
"""
from __future__ import annotations

SPAN = range(0, 8)


def _val(call, name: str, **kw):
    r = call(name, **kw)
    return r.value if r.ok else "%s %s" % (r.error.code, r.error.message)


def numbering(call) -> dict:
    """Read pattern count, active pattern, and per-index name, length and default state for indexes 0 to 7, plus playlist tracks."""
    out = {"pattern_count": _val(call, "op_patterns_pattern_count"), "pattern_number": _val(call, "op_patterns_pattern_number"), "patterns": {}}
    for i in SPAN:
        out["patterns"][i] = {"name": _val(call, "op_patterns_get_pattern_name", index=i), "length": _val(call, "op_patterns_get_pattern_length", index=i),
                              "default": _val(call, "op_patterns_is_pattern_default", index=i)}
    n = _val(call, "op_playlist_track_count")
    out["playlist_tracks"] = n
    if isinstance(n, int):
        out["track_names"] = {i: _val(call, "op_playlist_get_track_name", index=i) for i in (1, 2, n // 2, n)}
    out["non_default_indexes"] = [i for i, v in out["patterns"].items() if v["default"] == 0]
    out["passed"] = isinstance(n, int) and isinstance(out["pattern_count"], int)
    return out
