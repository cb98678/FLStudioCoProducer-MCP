from __future__ import annotations

import math

from coproducer.result import Result, fail, ok


def _skyline(notes: list[dict]) -> list[tuple]:
    top: dict = {}
    for n in notes:
        k = round(n["start"], 3)
        top[k] = max(top.get(k, 0), n["pitch"])
    s = sorted(top)
    return [(b - a, top[b] - top[a]) for a, b in zip(s, s[1:])]


def _similarity(a: list, b: list) -> float:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if x == y else 1)))
        prev = cur
    return 1.0 - prev[-1] / max(len(a), len(b), 1)


def compare_note_sequences(a: list[dict], b: list[dict], tolerance_beats: float = 0.125) -> Result:
    """Score how similar two note lists are, from 0 to 1, in ways that survive transposition and re-voicing.

    Scores: pitch_class (histogram cosine), melody (steps of the top line), rhythm (onset gaps), onsets (F1 of onset times).
    """
    if not a or not b:
        return fail("E_ARG", "both note lists need at least one note")
    ha, hb = [0.0] * 12, [0.0] * 12
    for h, notes in ((ha, a), (hb, b)):
        for n in notes:
            h[n["pitch"] % 12] += n["duration"]
    dot = sum(x * y for x, y in zip(ha, hb))
    cosine = dot / (math.sqrt(sum(x * x for x in ha)) * math.sqrt(sum(y * y for y in hb)))
    sa, sb = _skyline(a), _skyline(b)
    melody = _similarity([s for _, s in sa], [s for _, s in sb])
    rhythm = _similarity([round(g / tolerance_beats) for g, _ in sa], [round(g / tolerance_beats) for g, _ in sb])
    ta, tb = sorted({round(n["start"] / tolerance_beats) for n in a}), sorted({round(n["start"] / tolerance_beats) for n in b})
    hit = len(set(ta) & set(tb))
    f1 = 2 * hit / (len(ta) + len(tb))
    scores = {"pitch_class": round(cosine, 4), "melody": round(melody, 4), "rhythm": round(rhythm, 4), "onsets": round(f1, 4)}
    return ok({**scores, "overall": round(sum(scores.values()) / 4, 4)})
