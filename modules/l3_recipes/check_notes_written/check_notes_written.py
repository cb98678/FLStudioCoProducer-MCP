from __future__ import annotations

import json
from pathlib import Path

from coproducer.result import Result, fail, ok


def _wanted(notes: list, ppq: int) -> list:
    """The (pitch, tick, length, velocity) rows the script should have produced, in time order."""
    rows = [(n["pitch"], int(round(n["start"] * ppq)), max(1, int(round(n["duration"] * ppq))), round(n.get("velocity", 100) / 127, 4)) for n in notes]
    return sorted(rows, key=lambda r: (r[1], r[0]))


def check_notes_written(result_path: str, expected: int, notes: list | None = None) -> Result:
    """Read the result file the piano roll script left next to itself and confirm it wrote the expected notes.

    With notes given, every written note (pitch, tick, length, velocity within 0.01) is compared with what was asked for.
    Errors: E_NOT_FOUND when the script has not run, E_NOT_VERIFIED when counts or notes differ.
    """
    f = Path(result_path)
    if not f.is_file():
        return fail("E_NOT_FOUND", "no result file yet: run the script in FL (arm_piano_roll_script_gui, run_piano_roll_script_gui)")
    try:
        got = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read the result file: %s" % e)
    if got.get("written") != expected or got.get("expected") != expected:
        return fail("E_NOT_VERIFIED", "the script wrote %s of %d notes" % (got.get("written"), expected), report=got)
    if notes is not None:
        want, have = _wanted(notes, got.get("ppq", 96)), sorted((tuple(r) for r in got.get("notes", [])), key=lambda r: (r[1], r[0]))
        bad = [(w, h) for w, h in zip(want, have) if w[:3] != h[:3] or abs(w[3] - h[3]) > 0.01]
        if len(have) != len(want) or bad:
            return fail("E_NOT_VERIFIED", "%d of %d notes differ from what was asked for" % (len(bad), len(want)), first_difference=bad[:1])
    return ok(got, verified=True)
