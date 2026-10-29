"""Place a vocal cut on the words it is meant to hold, using a speech recogniser as the judge and the signal as the ruler.

Energy alone cannot tell a word boundary from the silent closure inside a word: the gap in "whis-KEY" before the k is quiet, but it is not the end of a word
(a cut there left "whis" and let "ky" leak into the next chop). A recogniser can tell, because a window that holds the whole word reads as that word and a window
that drops a syllable or keeps a leftover one does not. So:

    start: try each syllable onset or gap end near the hint; the first one whose window (cut start to a little past the hint end) reads as the expected words,
           with no leftover word in front, is the start.
    end:   try each onset or gap start near the hint, with a second of context before the cut; the first one whose window reads as the expected words
           at its tail is the end, i.e. the word is complete there.

Pure functions; the recogniser is passed in (tools/refine_cuts.py wraps Whisper), so the logic is testable without a model.
"""
from __future__ import annotations

import difflib
import re
from typing import Callable

import numpy as np

from . import vocalchops

Transcribe = Callable[[np.ndarray, int], str]

ALIASES = {"whisky": "whiskey", "okey": "okay", "ok": "okay", "i've": "i", "ive": "i"}
# Whisper starts a cold window with a filler word now and then ("The whiskey drowns" for a window that starts on "whiskey"). One of these in front is ignored;
# any other word in front is taken as a leftover from the previous word (the "Hey" of "-key" in front of "drowns").
STARTERS = {"the", "a", "and", "this", "it's", "it", "we're", "oh", "well", "so", "then", "but", "now", "that's", "in"}


def words(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9']+", text.lower()):
        w = w.strip("'")
        if w:
            out.append(ALIASES.get(w, w))
    return out


def _ratio(a: list[str], b: list[str]) -> float:
    return difflib.SequenceMatcher(None, "".join(a), "".join(b)).ratio()


def _best(t: list[str], e: list[str], head: bool) -> float:
    ns = range(1, min(len(t), len(e) + 1) + 1)
    return max((_ratio(t[:n] if head else t[-n:], e) for n in ns), default=0.0)


def head_match(transcript: str, expected: str, thresh: float = 0.75) -> bool:
    """The transcript starts with the expected words and nothing in front of them but at most one filler word (any other leading word is a leftover)."""
    t, e = words(transcript), words(expected)
    if not e or not t:
        return False
    if t[0] in STARTERS and e[0] not in STARTERS and len(t) > 1:
        t = t[1:]
    return _best(t, e, True) >= thresh and _ratio(t[:1], e[:1]) >= 0.6


def tail_match(transcript: str, expected: str, thresh: float = 0.75) -> bool:
    """The transcript ends with the expected words, whole."""
    t, e = words(transcript), words(expected)
    if not e or not t:
        return False
    return _best(t, e, False) >= thresh and _ratio(t[-1:], e[-1:]) >= 0.6


def candidates(x: np.ndarray, rate: int, gp: list[tuple[float, float]], lo: float, hi: float, role: str, preroll: float = 0.02, tail: float = 0.03, kind: str = "all") -> list[float]:
    """Cut candidates in [lo, hi]. A start sits just before a syllable onset or at the end of a gap; an end sits just before an onset or just after a gap starts.

    kind "gap" keeps only the gap-bounded ones. In sung words the quiet stretches (stop closures, breaths, the gate between phrases) are where words really part,
    so they are tried first and the onset-only candidates are the fallback.
    """
    ons = vocalchops.onsets(x, rate, max(0.0, lo - 0.1), hi + 0.1, min_gap=0.03) if kind == "all" else []
    if role == "start":
        c = [o - preroll for o in ons] + [g1 - preroll for g0, g1 in gp]
    else:
        c = [o - preroll for o in ons] + [g0 + tail for g0, g1 in gp]
    c = sorted(t for t in c if lo <= t <= hi)
    out: list[float] = []
    for t in c:
        if not out or t - out[-1] >= 0.02:
            out.append(round(t, 3))
    return out


def first_run(flags: list[bool], need: int = 2) -> int | None:
    """Index where the first run of `need` consecutive True values begins (a final lone True counts when it is the last item)."""
    for i, f in enumerate(flags):
        if f and (all(flags[i : i + need]) and len(flags[i : i + need]) == need or i == len(flags) - 1):
            return i
    return None


def _vote(passes: list[bool], need: int = 2) -> bool:
    return sum(passes) >= need


def voice_end(x: np.ndarray, rate: int, t: float, max_ahead: float = 1.0, drop_db: float = 6.0, hf_floor_db: float = -44.0, tail: float = 0.03) -> float:
    """Where the voice that is sounding at t really stops, for the last word of a phrase.

    A recogniser calls "okay" whole as soon as "o-kay" is under way, and a held "ay" or a trailing s goes on for another 0.2 to 0.6 s. The voice is over at the first
    window after t that is drop_db or more below the loudest of the last 0.3 s AND has no sibilance (4 to 12 kHz band under hf_floor_db). A new syllable that starts
    after the level has dipped ends the search at the dip. Returns the end plus a short tail.
    """
    w = 0.01
    lo = max(0.0, t - 0.3)
    seg = x[int(lo * rate) : int((t + max_ahead) * rate)]
    env, _ = vocalchops.envelope_db(seg, rate, w)
    hf = vocalchops.hf_db(seg, rate, w)[: len(env)]
    i0 = int((t - lo) / w)
    ref = float(env[: max(1, i0)].max())
    seen_dip = False
    for i in range(i0, len(env)):
        low = env[i] < ref - drop_db and (i >= len(hf) or hf[i] < hf_floor_db)
        if low and i + 1 < len(env) and env[i : i + 2].max() < ref - drop_db and hf[i : i + 2].max() < hf_floor_db:
            return lo + i * w + tail
        if env[i] < ref - drop_db:
            seen_dip = True
        elif seen_dip and env[i] > env[max(i0, i - 4) : i].min() + 6.0:
            return lo + max(i0, i - 4) * w + tail  # a new syllable begins after a dip
    return t


def sung_into(x: np.ndarray, rate: int, t: float, before: float = 0.15, floor_db: float = -45.0) -> bool:
    """True when the voice is already sounding in the `before` seconds ahead of t: the word at t is sung straight on from the note before."""
    env, _w = vocalchops.envelope_db(x[max(0, int((t - before) * rate)):int(t * rate)], rate, 0.01)
    return len(env) > 0 and float(np.median(env)) >= floor_db


def syllables(word: str) -> int:
    """A rough syllable count from the spelling: vowel groups, less a silent final e ("cause" 1, "lingo" 2, "inside" 2)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    n = len(re.findall(r"[aeiouy]+", w))
    if n > 1 and w.endswith("e") and not w.endswith(("le", "ee")):
        n -= 1
    return max(1, n)


def word_start(x: np.ndarray, rate: int, t0: float, t1: float, min_len: float = 0.7, hold: float = 0.25, semis: float = 1.5, before: float = 0.15,
               lead: float = 0.02, word: str = "") -> float:
    """Where a line's first word really starts when the recogniser stretched it back over the note held before it.

    Whisper gave "'cause" 43.18 to 44.68 s at the top of the first chorus of "Friends in Low Places", but the voice holds "complain" on one
    note (E4) until 44.2 s, so a cut at 43.18 opened the chorus and the hook chop with a second of "-plain". When the word is longer than
    min_len and the voice is already sounding in the `before` seconds ahead of t0 (sung straight on, no breath), the word starts where the
    pitch leaves the held note by `semis` semitones for two windows, or where the voice stops for three; t0 otherwise."""
    if word:
        min_len = max(min_len, 0.45 + 0.35 * syllables(word))  # a two-syllable word sung over two notes is not a stretched start ("lingo")
    if not min_len <= t1 - t0 <= 2.0:
        return t0                                       # short: trusted; over 2 s it is not one word (a part that starts before its first word)
    if not sung_into(x, rate, t0, before):
        return t0                                       # a breath before it: the recogniser's start is trusted
    times, f0 = vocalchops.pitch_track(x, rate, t0, t1 - 0.1)
    head = f0[times < t0 + hold]
    head = head[~np.isnan(head)]
    if len(head) < 5:
        return t0
    ref = float(np.median(head))
    off = np.where(np.isnan(f0), np.nan, np.abs(12 * np.log2(f0 / ref)))
    for i in range(int(np.searchsorted(times, t0 + hold)), len(f0) - 2):
        moved = not np.isnan(off[i]) and not np.isnan(off[i + 1]) and off[i] >= semis and off[i + 1] >= semis
        stopped = bool(np.isnan(f0[i:i + 3]).all())
        if moved or stopped:
            return float(times[i] - lead)
    return t0


def sibilant_end(x: np.ndarray, rate: int, e: float, cap: float = 0.15, drop_db: float = 5.0, hf_floor_db: float = -46.0) -> float:
    """If a cut ends just before a trailing s, extend it through the hiss (the s of "drowns" was cut off by 60 ms).

    The hiss counts only after the vowel has fallen at least drop_db, so a bright vowel is not mistaken for it.
    """
    w = 0.01
    seg = x[int(max(0.0, e - 0.25) * rate) : int((e + cap + 0.05) * rate)]
    env, _ = vocalchops.envelope_db(seg, rate, w)
    hf = vocalchops.hf_db(seg, rate, w)[: len(env)]
    i0 = int(min(0.25, e) / w)
    ref = float(env[: max(1, i0)].max())
    end, i, hole = i0, i0, 0
    while i < len(env) and (i - i0) * w <= cap:
        if hf[i] > hf_floor_db and env[i] < ref - drop_db:
            end, hole = i, 0
        else:
            hole += 1
            if hole > (3 if end > i0 else 7):  # up to 70 ms of nothing before the hiss starts, then bridge dips of 30 ms inside it
                break
        i += 1
    return e + (end - i0 + 1) * w if end > i0 else e

SIBILANT_STARTS = ("s", "z", "sh", "ch", "j")


def wants_final_s(spec: dict) -> bool:
    """True when the cut's last word ends in s and the word after it cannot supply a hiss of its own.

    spec["after"] names the words that follow the cut where `next` is not given (`next` also steers the recogniser, `after` only this rule).
    """
    if spec.get("tail") or spec.get("head"):
        return False  # a long clip ends where the voice stops (voice_end), not on a word boundary with a neighbour
    tail = words(spec.get("words") or "")
    if not tail or not tail[-1].endswith("s"):
        return False
    nxt = words(spec.get("next") or spec.get("after") or "")
    return not (nxt and nxt[0].startswith(SIBILANT_STARTS))


def final_s(x: np.ndarray, rate: int, e: float, reach: float = 0.45, hf_floor_db: float = -42.0, dominance_db: float = 16.0, prominence_db: float = 5.0,
            bridge: int = 2, tail: float = 0.015) -> float:
    """Carry an end through the closing s or z of a word like "blues", "places" or "friends".

    A sung final s often comes after the vowel has fallen or a short vowel has passed (the "iz" of "places"), 0.1 to 0.3 s after the point where the voice
    seems to stop, so the end rules above stop short of it. This finds the first hiss in reach after e (4 to 12 kHz level above hf_floor_db, within
    dominance_db of the total level so a bright vowel is not taken for it, and prominence_db above the quiet before it) and ends just after it, at the dip
    in front of the next word. If a hiss already ends within 60 ms before e, the cut has its s and e is returned unchanged.
    """
    w = 0.01
    a = max(0.0, e - 0.08)
    seg = x[int(a * rate) : int((e + reach + 0.05) * rate)]
    env, _ = vocalchops.envelope_db(seg, rate, w)
    hf = vocalchops.hf_db(seg, rate, w)[: len(env)]
    i0 = int(round((e - a) / w))

    def hiss(i: int) -> bool:
        return bool(hf[i] > hf_floor_db and hf[i] > env[i] - dominance_db)

    def onset(i: int) -> bool:  # a hiss starts as a clear rise out of the quiet before it; inside the hiss only the level test applies
        before = hf[max(0, i - 5) : i]
        return hiss(i) and (len(before) == 0 or bool(hf[i] >= float(before.min()) + prominence_db))

    if any(hiss(i) for i in range(max(0, i0 - 6), min(i0, len(env)))):
        return e
    i, last, start = max(i0, 0), None, None
    while i < len(env) and (i - i0) * w <= reach:
        if start is None:
            if onset(i):
                start = last = i
        elif hiss(i):
            last = i
        elif i - last > bridge:
            break
        i += 1
    return e if last is None else max(e, a + (last + 1) * w + tail)


def seam(x: np.ndarray, rate: int, cs: list[float], left: str | None, right: str | None, asr: Transcribe, right_to: Callable[[float], list[float]],
         left_ctx: tuple[float, ...] = (0.7, 1.0, 1.5)) -> tuple[dict, list]:
    """Judge every candidate cut point in cs on both sides, by vote over several window lengths (a recogniser alone is noisy on a few hundred ms of singing).

    left:  does the audio before the cut end on the words `left` (the previous word is whole)?
    right: does the audio after the cut begin on the words `right`, with no leftover syllable in front?
    Returns ({"left": index or None, "right": index or None}, evidence), where each index is where that side's first run of two passing candidates begins.
    """
    lo, ro, ev = [], [], []
    for c in cs:
        lts = [asr(x[int(max(0.0, c - w) * rate) : int(c * rate)], rate) for w in left_ctx] if left else []
        rts = [asr(x[int(c * rate) : int(t * rate)], rate) for t in right_to(c)] if right else []
        lo.append(_vote([tail_match(t, left) for t in lts], 2) if left else True)
        ro.append(_vote([head_match(t, right) for t in rts], 2) if right else True)
        ev.append([c, "|".join(t[-18:] for t in lts), "|".join(t[:18] for t in rts)])
    right1 = next((i for i, f in enumerate(ro) if f), None) if right else None  # first single pass, weaker than a run of two
    return {"left": first_run(lo) if left else None, "right": first_run(ro) if right else None, "right1": right1}, ev


def _with_tail(x: np.ndarray, rate: int, gp: list[tuple[float, float]], e: float, reach: float = 0.2, rise_db: float = 5.0) -> float:
    """If the voice only decays between e and the start of the next gap (no new syllable rises in between), the cut belongs at the gap.

    The recogniser cannot hear the voiced z of "blues" or the end of a held vowel, so an end it accepts can sit 0.1 s too early.
    """
    nxt = [g0 + 0.03 for g0, g1 in gp if e + 0.01 < g0 + 0.03 <= e + reach]
    if not nxt:
        return e
    g = min(nxt)
    env, _ = vocalchops.envelope_db(x[int(e * rate) : int(g * rate)], rate, 0.01)
    if len(env) < 2:
        return e
    rise = float(np.max(env - np.minimum.accumulate(env)))
    return g if rise < rise_db else e


def _with_hiss(x: np.ndarray, rate: int, gp: list[tuple[float, float]], e: float) -> float:
    """Extend an end through a trailing s, unless it already sits on a gap boundary (gaps are measured with the hiss counted as sound)."""
    if any(abs(e - (g0 + 0.03)) < 0.006 or abs(e - (g1 - 0.02)) < 0.006 for g0, g1 in gp):
        return e
    return sibilant_end(x, rate, e)


def _pick_start(runs: dict, cs: list[float]) -> int | None:
    ri, li = runs["right"], runs["left"]
    r1 = runs.get("right1")
    if ri is None and r1 is not None and (li is None or cs[r1] < cs[li] - 0.05):
        return r1  # one clean reading of the cut's own words, earlier than where the left side was confirmed: the left reading is the noisier one
    if ri is not None and li is not None and cs[li] > cs[ri]:
        t = min(cs[li], cs[ri] + 0.12)  # the previous word is not whole yet: nudge later, but not far, since the left reading is the noisier one
        return max(i for i, c in enumerate(cs) if c <= t)
    return ri if ri is not None else li


RANK = {"none": 0, "left": 1, "right": 2, "both": 3}


def _kind(runs: dict) -> str:
    li, ri = runs["left"], runs["right"]
    return "both" if li is not None and ri is not None else ("left" if li is not None else ("right" if ri is not None else "none"))


def refine(x: np.ndarray, rate: int, gp: list[tuple[float, float]], spec: dict, asr: Transcribe, reach: float = 0.5) -> dict:
    """Refine one cut. spec: start, end (hints, seconds), words (or head/tail for a long clip), prev and next (the words just outside each edge, if known).

    Start: the first candidate where the audio from there reads as the cut's own words with no leftover in front (the leftover "ky" of "whiskey" in front of
    "drowns" fails this), and, if the previous word is known, no earlier than where that word is whole. Gap-bounded candidates are tried before onset-only ones.
    End with a next word: the first candidate where the audio up to there ends on the cut's last word, whole, and the next word starts clean; a trailing s is then
    included. End without one (a phrase ends in silence): where the recogniser says the last word is whole, then on to where the voice really stops (voice_end),
    because a held vowel or an s outlasts the moment the recogniser is satisfied.
    """
    head = spec.get("head") or spec.get("words")
    tail_words = spec.get("tail") or spec.get("words")
    out: dict = {"hint": [spec["start"], spec["end"]], "evidence": {}}
    onsets_all = vocalchops.onsets(x, rate, spec["start"] - 1, spec["end"] + 1.5, 0.05)
    # --- start
    best, ev = None, []
    if head:
        for ck in ("gap", "all"):
            cs = candidates(x, rate, gp, spec["start"] - reach, spec["start"] + reach, "start", kind=ck)
            if not cs:
                continue
            runs, e2 = seam(x, rate, cs, spec.get("prev"), head, asr, lambda c: [spec["end"] + d for d in (0.3, 0.6, 0.9)])
            ev += e2
            idx = _pick_start(runs, cs)
            if idx is not None and (best is None or RANK[_kind(runs)] > RANK[best[2]]):
                best = (cs[idx], ck, _kind(runs))
            if best is not None and best[2] == "both":
                break
    out["evidence"]["start"] = ev
    out["start_ok"] = best is not None
    out["start_kind"] = best[2] if best else "none"
    out["start"] = best[0] if best else vocalchops.snap_start(onsets_all, spec["start"])
    # --- end
    lo_, hi_ = max(out["start"] + 0.2, spec["end"] - reach), spec["end"] + reach
    ctx = (max(0.7, spec["end"] - out["start"] + 0.5), max(1.0, spec["end"] - out["start"] + 1.0), max(1.5, spec["end"] - out["start"] + 1.5))
    j, ekind, ce, li = None, "none", [], None
    ev = []
    if tail_words:
        for ck in ("gap", "all"):
            ce = sorted(set(candidates(x, rate, gp, lo_, hi_, "end", kind=ck) + (candidates(x, rate, gp, lo_, hi_, "start", kind=ck) if spec.get("next") else [])))
            if not ce:
                continue
            runs, e2 = seam(x, rate, ce, tail_words, spec.get("next"), asr, lambda c: [c + d for d in (0.8, 1.2, 1.6)], left_ctx=ctx)
            ev += e2
            li, ri = runs["left"], runs["right"]
            if li is not None and ri is not None:
                t = max(ce[li], min(ce[ri], ce[li] + 0.4))
                j = max(i for i, c in enumerate(ce) if c <= t)
            else:
                j = li if li is not None else ri
            ekind = _kind(runs)
            if ekind == "right" and abs(ce[j] - spec["end"]) > 0.25:
                j, ekind = None, "none"  # a reading of the next word alone, far from where the cut should end, is more likely noise than a boundary
            if j is not None:
                break
    out["evidence"]["end"] = ev
    out["end_ok"] = j is not None
    out["end_kind"] = ekind
    if j is not None:
        e = ce[j]
        if not spec.get("next"):
            e = max(e, voice_end(x, rate, e))
        out["end"] = _with_hiss(x, rate, gp, _with_tail(x, rate, gp, e))
    else:
        e = vocalchops.snap_end(onsets_all, gp, spec["end"], spec.get("end_mode", "word"))
        out["end"] = _with_hiss(x, rate, gp, _with_tail(x, rate, gp, e))
    out["final_s"] = False
    if wants_final_s(spec):
        e2 = final_s(x, rate, out["end"])
        out["final_s"] = e2 > out["end"]
        out["end"] = e2
    out["end"] = max(out["end"], out["start"] + 0.15)
    return out
