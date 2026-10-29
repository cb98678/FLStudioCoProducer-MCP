from __future__ import annotations

from pathlib import Path

from coproducer.pianoroll_template import render_script
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _rows(notes: list) -> list | None:
    """Notes {pitch, start, duration, velocity} in beats (velocity 0 to 127) as script rows, or None when any note is invalid."""
    rows = []
    for n in notes:
        ok_note = 0 <= n.get("pitch", -1) <= 127 and n.get("start", -1) >= 0 and n.get("duration", 0) > 0
        if not ok_note:
            return None
        rows.append([n["pitch"], n["start"], n["duration"], round(n.get("velocity", 100) / 127, 4), 0.5])
    return rows


def write_notes_via_script(notes: list, name: str = "coproducer_notes", clear_first: bool = True) -> Result:
    """Generate the piano roll script that writes these notes and install it in FL's Piano roll scripts folder.

    The script reports back through a result file next to itself (FL scripts can only write in their own folder), so the
    host reads it from the same folder. Nothing is written to the project yet: arm_piano_roll_script_gui and
    run_piano_roll_script_gui run it, then check_notes_written confirms. Errors: E_ARG for an invalid note,
    E_UNSUPPORTED_API without a scripts folder.
    """
    rows, folder = _rows(notes), get_service("piano_roll_scripts_dir")
    if rows is None or not rows:
        return fail("E_ARG", "every note needs pitch 0 to 127, start >= 0 and duration > 0, and there must be at least one note")
    if not folder:
        return fail("E_UNSUPPORTED_API", "no Piano roll scripts folder is configured; set [fl] data_dir in config.toml")
    folder = Path(str(folder))
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / (name + ".result.json")
    result.unlink(missing_ok=True)
    target = folder / (name + ".pyscript")
    target.write_text(render_script(rows, clear_first, result.name), encoding="utf-8", newline="\n")
    ok_file = target.is_file() and target.stat().st_size > 0
    return ok({"script": name, "path": str(target), "result_path": str(result), "expected": len(rows), "ppq_assumed": 96}, verified=ok_file)
