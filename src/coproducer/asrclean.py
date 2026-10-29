"""Whisper's repetition loops on sung vocals: found, redone window by window on the vocal's own phrases, and spliced back.

Whisper large-v3 can fall into a loop over long stretches of singing with music under it: one word written hundreds of times, or hundreds
of words a few hundredths of a second long (Girlish Type Men, 2026-10-29: one token 206 times in a row over 42 bars, then 314 words of
0.08 s in 21 s). A loop is not a lyric: songform reads its repeats as a chorus and the cutters cut on its invented word times. loop_spans
finds the loops, windows plans short windows over them on the vocal stem's phrases (short-form Whisper does not carry text from one
window to the next), and splice puts the redone words in; a window that loops again keeps no words (the voice is still there, its words
unknown), which is said in the report.
"""
from __future__ import annotations

import re

MAX_RUN = 8            # the same word more than this many times in a row is a loop
MIN_MEAN_DUR = 0.12    # s: a stretch of words this short on average is not sung words
STRETCH = 20           # how many words that mean is taken over
WINDOW_MAX_S = 12.0    # longest redo window
MARGIN_S = 0.15        # added on both sides of a window so a first or last consonant is not clipped


def _norm(w) -> str:
    return re.sub(r"[^a-z']", "", str(w).lower())


def _end(x: dict) -> float:
    return float(x["end"]) if x.get("end") is not None else float(x["start"]) + 0.3


def merge(spans: list, pad: float = 0.0) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in sorted((float(a) - pad, float(b) + pad) for a, b in spans):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def loop_spans(words: list[dict], max_run: int = MAX_RUN, min_mean: float = MIN_MEAN_DUR, stretch: int = STRETCH) -> list[tuple[float, float]]:
    """(start, end) seconds of each stretch that looks like a loop: a word repeated more than max_run times in a row, or stretch words whose
    mean length is under min_mean."""
    spans = []
    toks = [_norm(x.get("word", "")) for x in words]
    i = 0
    while i < len(words):
        j = i
        while j + 1 < len(words) and toks[i] and toks[j + 1] == toks[i]:
            j += 1
        if j - i + 1 > max_run:
            spans.append((words[i]["start"], _end(words[j])))
        i = j + 1
    for i in range(0, max(0, len(words) - stretch + 1)):
        seg = words[i:i + stretch]
        if sum(_end(x) - float(x["start"]) for x in seg) / len(seg) < min_mean:
            short = [x for x in seg if _end(x) - float(x["start"]) < 2 * min_mean]   # the loop's own words, not the real ones beside it
            spans.append((short[0]["start"], _end(short[-1])))
    return merge(spans)


def windows(spans: list, phrases: list[dict], max_s: float = WINDOW_MAX_S, margin: float = MARGIN_S) -> list[list[float]]:
    """Redo windows over the loop spans: the vocal's phrases ({start, end} from vocalchops.phrases) that overlap a span, clipped to it,
    neighbours joined while they fit max_s, a longer phrase split into max_s pieces. Without phrases the span itself is split."""
    out: list[list[float]] = []
    for a, b in spans:
        parts = [(max(a, p["start"]), min(b, p["end"])) for p in phrases if p["end"] > a and p["start"] < b] or [(a, b)]
        cur = None
        for s, e in parts:
            while e - s > max_s:
                if cur:
                    out.append(list(cur))
                    cur = None
                out.append([s, s + max_s])
                s += max_s
            if cur and e - cur[0] <= max_s:
                cur = (cur[0], e)
            else:
                if cur:
                    out.append(list(cur))
                cur = (s, e)
        if cur:
            out.append(list(cur))
    return [[round(max(0.0, s - margin), 3), round(e + margin, 3)] for s, e in out if e - s > 0.2]


def splice(words: list[dict], spans: list, redone: list[dict]) -> tuple[list[dict], dict]:
    """The words outside the loop spans plus the redone words inside them, in time order; redone words that loop again are dropped.
    Returns (words, report)."""
    def inside(x, sp):
        mid = (float(x["start"]) + _end(x)) / 2
        return any(a <= mid <= b for a, b in sp)
    kept = [x for x in words if not inside(x, spans)]
    groups: list[list[dict]] = []   # one redo window's words each: a loop is judged inside its own window, not across the gap to the next
    for x in sorted(redone, key=lambda w: float(w["start"])):
        if groups and float(x["start"]) - _end(groups[-1][-1]) <= 1.0:
            groups[-1].append(x)
        else:
            groups.append([x])
    again = merge([sp for g in groups for sp in loop_spans(g)])
    new = [x for x in redone if inside(x, spans) and not inside(x, again)]
    out = sorted(kept + new, key=lambda x: float(x["start"]))
    rep = {"loop_spans": [[round(a, 2), round(b, 2)] for a, b in spans], "removed": len(words) - len(kept), "redone": len(new),
           "still_looping": [[round(a, 2), round(b, 2)] for a, b in again],
           "seconds_without_words": round(sum(b - a for a, b in again), 2)}
    return out, rep
