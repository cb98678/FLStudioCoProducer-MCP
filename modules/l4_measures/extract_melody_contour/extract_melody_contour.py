from __future__ import annotations

from coproducer.result import Result, fail, ok


def extract_melody_contour(notes: list[dict], voice: str = "top") -> Result:
    """Reduce a note list to one melodic line (the top or bottom note at each onset) and describe its shape.

    Returns pitches, semitone steps, gaps between onsets in beats, and a string of U (up), D (down), R (repeat).
    """
    if not notes:
        return fail("E_ARG", "the note list is empty")
    pick = max if voice == "top" else min
    onsets: dict = {}
    for n in notes:
        onsets.setdefault(round(n["start"], 4), []).append(n["pitch"])
    starts = sorted(onsets)
    pitches = [pick(onsets[s]) for s in starts]
    steps = [b - a for a, b in zip(pitches, pitches[1:])]
    gaps = [round(b - a, 4) for a, b in zip(starts, starts[1:])]
    shape = "".join("U" if d > 0 else "D" if d < 0 else "R" for d in steps)
    return ok({"starts": starts, "pitches": pitches, "steps": steps, "gaps": gaps, "contour": shape})
