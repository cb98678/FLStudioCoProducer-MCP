from __future__ import annotations

from coproducer import soundbrief
from coproducer.result import Result, fail, ok


def compare_part_sound(original: str, remake: str, original_start_s: float = 0.0, original_end_s: float = 0.0,
                       remake_start_s: float = 0.0, remake_end_s: float = 0.0) -> Result:
    """Measure both parts (measure_part_sound's reading) and return the differences (attack, decay, sustain, release as ratios or
    steps, brightness, harmonic fall, odd against even, width, register) with what to change on the patch (edit_preset).

    Errors: E_IO (a file unreadable or too short), E_NOT_FOUND (no notes in one of them).
    """
    sounds = []
    for path, a, b in ((original, original_start_s, original_end_s), (remake, remake_start_s, remake_end_s)):
        try:
            x, rate = soundbrief.load_slice(path, a, b)
        except ValueError as e:
            return fail("E_IO", "%s: %s" % (path, e))
        d = soundbrief.describe(x, rate)
        if not d.get("measured"):
            return fail("E_NOT_FOUND", "no notes found in %s" % path)
        sounds.append(d)
    out = soundbrief.compare(sounds[0], sounds[1])
    return ok({**out, "original": sounds[0], "remake": sounds[1]})
