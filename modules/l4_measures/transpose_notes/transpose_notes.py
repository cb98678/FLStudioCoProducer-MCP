from __future__ import annotations

from coproducer.result import Result, fail, ok


def transpose_notes(notes: list[dict], semitones: int, fold_octaves: bool = False) -> Result:
    """Shift every note's pitch by semitones. With fold_octaves, out-of-range notes move by whole octaves to fit.

    Errors: E_ARG when a shifted pitch falls outside 0 to 127 and fold_octaves is false.
    """
    out = []
    for n in notes:
        p = n["pitch"] + semitones
        while fold_octaves and p > 127:
            p -= 12
        while fold_octaves and p < 0:
            p += 12
        if not 0 <= p <= 127:
            return fail("E_ARG", "pitch %d moves to %d, outside 0 to 127" % (n["pitch"], p), pitch=n["pitch"])
        out.append({**n, "pitch": p})
    return ok(out)
