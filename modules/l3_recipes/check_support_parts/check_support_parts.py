from __future__ import annotations

from coproducer import arranger
from coproducer.result import Result, fail, ok


def check_support_parts(parts: dict, sung: list, cells: dict | None = None) -> Result:
    """Measure parts (role -> [start_beat, dur_beats, key, velocity] notes; roles pad, keys, bass, answer) against the session-arranger
    rules: polyphony and notes per bar under each role's limit, starts on the role's grid, bass starts only where its cells (bar -> cell
    name, 0-based bars) put them plus the approach on the last 8th, velocities louder on downbeats with a spread and none at 127, and no
    answer note while she sings (sung: one flag per 16th from beat 0). Errors: E_ARG (an unknown cell)."""
    cells = {int(b): c for b, c in (cells or {}).items()}
    if any(c not in arranger.CELLS for c in cells.values()):
        return fail("E_ARG", "unknown bass cell; cells: %s" % ", ".join(arranger.CELLS))
    got = arranger.check({k: [tuple(n) for n in v] for k, v in parts.items()}, {"sung": list(sung), "onsets": []}, cells or None)
    return ok(got)
