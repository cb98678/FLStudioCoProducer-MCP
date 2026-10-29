from __future__ import annotations

from coproducer import soundbrief
from coproducer.result import Result, fail, ok


def measure_part_sound(path: str, start_s: float = 0.0, end_s: float = 0.0, role: str = "", name: str = "", max_notes: int = 12) -> Result:
    """Read one stem of the original (or a stretch of it) the way a sound designer would: how its notes start, hold, decay and end,
    how bright they are and how that moves, which harmonics lead and how fast they fall, noise, grit, width and register. Returns the
    measurements with plain words for the creative brief and a first serum-mcp preset draft to design from (generate_preset).

    Errors: E_IO (unreadable or too short), E_ARG (end before start), E_NOT_FOUND (no notes above the floor).
    """
    if end_s and end_s <= start_s:
        return fail("E_ARG", "end_s must be after start_s")
    try:
        x, rate = soundbrief.load_slice(path, start_s, end_s)
    except ValueError as e:
        return fail("E_IO", str(e))
    sound = soundbrief.describe(x, rate, max_notes=max_notes)
    if not sound.get("measured"):
        return fail("E_NOT_FOUND", "no notes found in that stretch", sound=sound)
    return ok({"sound": sound, "starting_point": soundbrief.starting_point(sound, role, name)})
