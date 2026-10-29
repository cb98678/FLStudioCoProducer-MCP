from __future__ import annotations

from coproducer.result import Result, ok


def clean_midi_notes(notes: list[dict], min_duration: float = 0.05, min_velocity: int = 5) -> Result:
    """Remove very short and very quiet notes, and shorten notes that overlap a later note of the same pitch.

    The value holds the cleaned notes; meta lists how many were removed and how many were trimmed.
    """
    kept = [n for n in notes if n["duration"] >= min_duration and n.get("velocity", 100) >= min_velocity]
    kept.sort(key=lambda n: (n["pitch"], n["start"]))
    trimmed, out = 0, []
    for i, n in enumerate(kept):
        nxt = kept[i + 1] if i + 1 < len(kept) and kept[i + 1]["pitch"] == n["pitch"] else None
        if nxt and n["start"] + n["duration"] > nxt["start"]:
            n = {**n, "duration": round(nxt["start"] - n["start"], 6)}
            trimmed += 1
        if n["duration"] >= min_duration:
            out.append(n)
    out.sort(key=lambda n: (n["start"], n["pitch"]))
    return ok(out, removed=len(notes) - len(out), trimmed=trimmed)
