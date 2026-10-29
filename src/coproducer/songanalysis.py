"""Song analysis for the remix pipeline: turn the facts about one song (drum hits, vocal words, bar levels) into the fields of a song plan.

Everything here works on data that the tools already produce: `drumhits` hits for the downbeat, Whisper word times for the lyrics, per-bar levels for the
sections. Nothing loads audio, so each step is testable on a small fixture and the same code runs on a second song. The regression is the first song: the chop
planner has to find the hook, friends, low places, whiskey drowns, my blues away and I'll be okay that were picked by hand (tests/test_songanalysis.py).
Word times from Whisper drift on sung vocals, so the windows here are starting points; `tools/refine_cuts.py` snaps them to the audio.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import numpy as np

STOP = frozenset("""a an and are as at be but by cause cos did do for from got had has have he her him his i i'd i'll i'm i've if in is it its me my no not of oh on or
she so that the their them then there they this to too up was we well were what when where who will with yeah you your you'll you're you've""".split())
MAX_WORD_S, MIN_SPAN_S, MAX_SPAN_S = 2.0, 0.25, 3.8   # a word longer than 2 s is a bad Whisper time, not a held note


def tokens(words: list[dict]) -> list[dict]:
    """Lower-case word records {w, t0, t1} from Whisper word entries ({word, start, end}) in time order; empty words are dropped.

    Whisper transcribes a long file in overlapping windows, and the words file holds both windows' words where they overlap (Friends in Low
    Places: the words jump back from 69 s to 60 s and from 250 s to 240 s, so "i'm not big on social graces" read "i'm i'm not not big big
    ..."). Words of one pass never overlap in time, so a word that overlaps one already kept by half of the shorter one's length, or the same
    word (or its plural) overlapping at all, is the other window's copy and is dropped."""
    out: list[dict] = []
    for w in sorted(words, key=lambda w: (float(w["start"]), float(w["end"]))):
        n = re.sub(r"[^a-z']", "", str(w["word"]).lower())
        t0, t1 = float(w["start"]), float(w["end"])
        if not n or t1 - t0 < 0.03:   # Whisper gives some invented words no time at all
            continue
        dup = None
        for k in out[-4:]:
            ov = min(t1, k["t1"]) - max(t0, k["t0"])
            same = n.replace("'", "").rstrip("s") == k["w"].replace("'", "").rstrip("s")
            if (same and ov > 0.02) or ov >= 0.5 * min(t1 - t0, k["t1"] - k["t0"]):
                dup = k
                break
        if dup is None:
            out.append({"w": n, "t0": t0, "t1": t1})
            continue
        if n.endswith("s") and not dup["w"].endswith("s") and n[:-1] == dup["w"]:
            dup["w"] = n                        # one window heard "grace", the other "graces": keep the whole word
        if t1 - t0 < dup["t1"] - dup["t0"]:     # a window's first word is stretched back to the window's start: keep the tighter copy's times
            dup["t0"], dup["t1"] = t0, t1
    out.sort(key=lambda t: t["t0"])
    k = 2                                       # a two-word copy that did not overlap: "i've got i've got" inside a second at a window's start
    while k + 1 < len(out):
        a, b, c, d = out[k - 2], out[k - 1], out[k], out[k + 1]
        if a["w"] != b["w"] and (c["w"], d["w"]) == (a["w"], b["w"]) and d["t1"] - a["t0"] < 1.5:
            b["t1"] = max(b["t1"], d["t1"])     # the first window cut the word off at its edge; the copy shows how long it was sung
            del out[k:k + 2]
        else:
            k += 1
    return out


def _valid(span: list[dict]) -> bool:
    dur = span[-1]["t1"] - span[0]["t0"]
    return MIN_SPAN_S <= dur <= MAX_SPAN_S and all(t["t1"] - t["t0"] <= MAX_WORD_S for t in span)


def _content_key(span: list[dict]) -> tuple:
    """The sung words without the little words, so 'friends in the low places' and 'friends in low places' count as the same line."""
    return tuple(t["w"] for t in span if t["w"] not in STOP)


def _edges_ok(span: list[dict]) -> bool:
    return span[0]["w"] not in STOP and span[-1]["w"] not in STOP


def repeated_spans(toks: list[dict], n_max: int = 7) -> dict[tuple, list[tuple[int, int]]]:
    """{content words: [(start index, length)]} for every run of up to n_max words that starts and ends on a content word, has a plausible duration, and
    comes back at least twice without overlapping itself. Runs that differ only in little words share a key."""
    found: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    for n in range(1, n_max + 1):
        for i in range(len(toks) - n + 1):
            span = toks[i:i + n]
            if not (_valid(span) and _edges_ok(span)):
                continue
            hits = found[_content_key(span)]
            if all(i >= j + m or i + n <= j for j, m in hits):
                hits.append((i, n))
    return {k: v for k, v in found.items() if len(v) >= 2}


def _isolation(toks: list[dict], i: int, n: int) -> float:
    """Seconds of quiet before and after a run of words (each capped at 0.6 s): a run with air around it is easy to cut cleanly."""
    before = toks[i]["t0"] - toks[i - 1]["t1"] if i > 0 else 0.6
    after = toks[i + n]["t0"] - toks[i + n - 1]["t1"] if i + n < len(toks) else 0.6
    return min(max(before, 0.0), 0.6) + min(max(after, 0.0), 0.6)


def _window(toks: list[dict], where: list[tuple[int, int]]) -> dict:
    """The most isolated occurrence (the later one on a tie), as a chop spec: start, end, the sung words and their neighbours."""
    i, n = max(where, key=lambda w: (round(_isolation(toks, *w), 2), w[0]))
    gap = toks[i + n]["t0"] - toks[i + n - 1]["t1"] if i + n < len(toks) else 1.0
    spec = {"start": round(toks[i]["t0"], 2), "end": round(toks[i + n - 1]["t1"], 2), "end_mode": "word", "words": " ".join(t["w"] for t in toks[i:i + n])}
    if i > 0:
        spec["prev"] = toks[i - 1]["w"]
    if i + n < len(toks):
        spec["next" if n <= 2 else "after"] = toks[i + n]["w"]
    spec["_gap"] = round(gap, 2)   # air after the last word; a piece of two words or more is only a clean cut when it ends in air
    return spec


def rank_spans(toks: list[dict], n_max: int = 7, title: str = "") -> list[dict]:
    """Candidate chops, best first. Score is repeats times content words to the 1.5 (a long line that comes back beats its parts, a word sung in every chorus
    beats a rare one). With a title, spans that hold two or more of its content words get a bonus by how much of the title they cover, so the hook is the
    title line. Each row: {key, count, content, score, title_share, spec}."""
    want = {w for w in re.findall(r"[a-z']+", title.lower()) if w not in STOP}
    rows = []
    for key, where in repeated_spans(toks, n_max).items():
        share = len(want & set(key)) / len(want) if want else 0.0
        score = len(where) * len(key) ** 1.5 + (100.0 * share if len(want & set(key)) >= 2 else 0.0)
        rows.append({"key": key, "count": len(where), "content": len(key), "score": score, "title_share": round(share, 2), "where": where, "spec": _window(toks, where)})
    return sorted(rows, key=lambda r: (-r["score"], len(r["key"])))


def _overlap(a: dict, b: dict) -> float:
    return max(0.0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def _slug(key: tuple, taken: set) -> str:
    base = "".join(re.sub(r"[^a-z]", "", w) for w in key[:2]) or "chop"
    name, i = base, 2
    while name in taken:
        name, i = "%s%d" % (base, i), i + 1
    return name


def plan_chops(toks: list[dict], title: str = "", max_chops: int = 12) -> dict:
    """Choose the chops: the hook (the best repeated line of 3 or more sung words, the title line when a title is given), then the best repeated pieces of one to
    three words that are sung in at least two of the hook's choruses (the 18 seconds from just before each hook), one name each, in score order. Returns
    {"chops": {name: spec}, "hook": "hook", "pieces": [names, best first], "ranked": rows}. The window of each chop is its most isolated occurrence;
    refine_cuts snaps it to the audio."""
    ranked = rank_spans(toks, title=title)
    hooks = [r for r in ranked if len(r["spec"]["words"].split()) >= 3 and r["content"] >= 2]
    if not hooks:
        raise ValueError("no repeated line of 3 or more words found in the lyrics")
    windows = [(toks[i]["t0"] - 2.0, toks[i]["t0"] + 16.0) for i, _n in hooks[0]["where"]]

    def choruses_with(where: list) -> int:
        return len({k for i, _n in where for k, (a, b) in enumerate(windows) if a <= toks[i]["t0"] <= b})

    chops, taken, seen, pieces = {"hook": hooks[0]["spec"]}, {"hook"}, {hooks[0]["key"]}, []
    cands = [r for r in ranked if r["key"] not in seen and r["content"] <= 2 and len(r["spec"]["words"].split()) <= 3 and choruses_with(r["where"]) >= 2
             and (len(r["spec"]["words"].split()) == 1 or r["spec"]["_gap"] >= 0.08)]
    for r in sorted(cands, key=lambda r: (-choruses_with(r["where"]), -r["count"], r["content"], r["spec"]["start"])):
        if len(chops) >= max_chops:
            break
        name = _slug(r["key"], taken)
        chops[name], taken = r["spec"], taken | {name}
        pieces.append(name)
    for spec in chops.values():
        spec.pop("_gap", None)
    return {"chops": chops, "hook": "hook", "pieces": pieces, "ranked": ranked}


def assign_roles(plan: dict, closer_word: str = "") -> dict:
    """The chop roles `arrange.arrange_chops` needs, from the planned chops. Pieces of the hook tease it in the intro (those nearest a second long) and one of
    them is the build stab; other chorus words stutter in the builds (those nearest half a second) and answer the hook; the piece named closer_word, the last
    sung word of the chorus, closes the drops and the outro. The hook and every piece of 0.6 s or more get an echo variant. Returns {"roles", "echoed"}."""
    chops, pieces = plan["chops"], list(plan["pieces"])
    if len(pieces) < 5:
        raise ValueError("need at least five repeated pieces to give every role a chop, found %d" % len(pieces))
    dur = {n: chops[n]["end"] - chops[n]["start"] for n in pieces}
    hook_words = set(re.sub(r"[^a-z']", "", w) for w in chops["hook"]["words"].split())
    inside = [n for n in pieces if set(chops[n]["words"].split()) <= hook_words]
    outside = [n for n in pieces if n not in inside]
    near = lambda target: (lambda n: (abs(dur[n] - target), pieces.index(n)))  # noqa: E731
    teach = sorted(inside, key=near(1.0)) + sorted(outside, key=near(1.0))
    stut = sorted(outside, key=near(0.55)) + sorted(inside, key=near(0.55))
    echoed = ["hook"] + [n for n in pieces if dur[n] >= 0.6]
    echo = lambda n: n + "_echo" if n in echoed else n  # noqa: E731
    closer = closer_word if closer_word in pieces else pieces[-1]
    tease, (a_, b_) = teach[:3], stut[:2]
    answers = [n for n in pieces if n not in tease + [a_, b_]] or pieces
    roles = {"teasers": [tease[0], echo(tease[1]), tease[2]], "hook": "hook", "hook_echo": echo("hook"),
             "groove_answers": [echo(n) if i % 2 == 0 else n for i, n in enumerate(answers[:4])], "groove_tail": echo(tease[1]),
             "stutter_a": a_, "stutter_b": b_, "stab": tease[0], "stab_echo": echo(tease[0]),
             "drop_answers": [echo(answers[0]), answers[-1]], "closers": [closer, echo(closer)], "outro_closer": echo(closer)}
    return {"roles": roles, "echoed": echoed}


def find_downbeat(hits: list[dict], bpm: float, offset: float, entrance_s: float = 1.5) -> dict:
    """Which 16th step of the detected grid is the first beat of the bar. Every candidate step scores the strength of kicks on it (1.0) and half a bar later
    (0.6) and of snares a beat after and a beat before the half bar (0.75), plus 2.0 for a hit that comes in after at least entrance_s of silence, since a
    drum part enters on a bar line. A backbeat pattern cannot tell beat one from beat three; the entrance rule breaks that tie. Returns {"step", "origin_s"
    (the bar line at or just before the first hit), "confidence" (the winner's lead over the runner-up), "scores"}."""
    step = 60.0 / bpm / 4
    score = np.zeros(16)
    last = -1e9
    for h in sorted(hits, key=lambda h: h["t"]):
        pos = int(round((h["t"] - offset) / step))
        entrance = h["t"] - last >= entrance_s
        for q in range(16):
            k = (pos - q) % 16
            if h["kind"] == "kick":
                score[q] += h["s"] * (1.0 if k == 0 else 0.6 if k == 8 else 0.0)
            elif h["kind"] == "snare":
                score[q] += 0.75 * h["s"] * (1.0 if k in (4, 12) else 0.0)
            if entrance and k == 0:
                score[q] += 2.0 * h["s"]
        last = h["t"]
    q = int(np.argmax(score))
    first = min((h["t"] for h in hits), default=offset)
    bar = 16 * step
    n = int(np.floor((first + 0.5 * step - offset - q * step) / bar))
    srt = np.sort(score)
    conf = float((srt[-1] - srt[-2]) / srt[-1]) if srt[-1] > 0 else 0.0
    return {"step": q, "origin_s": round(offset + q * step + n * bar, 4), "confidence": round(conf, 2), "scores": [round(float(v), 1) for v in score]}


def hit_rows(rows: list[list]) -> list[dict]:
    """drum_hits.json rows [t, kind, strength] as {t, kind, s}."""
    return [{"t": float(r[0]), "kind": r[1], "s": float(r[2])} for r in rows]


def sections_from_bars(bar_db: list[float], vocal_bars: set[int], hook_bars: set[int], min_bars: int = 4, step_db: float = 2.5) -> list[dict]:
    """Split a song into sections of at least min_bars bars where the smoothed bar level jumps by step_db, then label each: chorus when it holds the hook, verse
    when there is a vocal, intro or outro for an unsung start or end, break for an unsung middle. Returns [{start, end, label, db}] in bars."""
    if not bar_db:
        return []
    x = np.asarray(bar_db, dtype=float)
    lo, hi = min_bars, len(x) - min_bars
    jump = {b: abs(x[b:b + min_bars].mean() - x[b - min_bars:b].mean()) for b in range(lo, hi + 1)}
    cuts = [0]
    for b in sorted(jump, key=lambda b: (-jump[b], b)):      # greedy: the biggest jump first, then the next one at least min_bars away
        if jump[b] < step_db:
            break
        if all(abs(b - c) >= min_bars for c in cuts):
            cuts.append(b)
    cuts = sorted(cuts)
    cuts.append(len(x))
    out = []
    for s, e in zip(cuts, cuts[1:]):
        bars = set(range(s, e))
        sung = len(bars & vocal_bars) / len(bars) >= 0.4
        label = "chorus" if bars & hook_bars else "verse" if sung else "intro" if s == 0 else "outro" if e == len(x) else "break"
        out.append({"start": s, "end": e, "label": label, "db": round(float(x[s:e].mean()), 1)})
    return out


def bars_with_words(toks: list[dict], bpm: float, origin_s: float) -> set[int]:
    """Bar numbers (0 at origin_s) in which something is sung."""
    bar_s = 240.0 / bpm
    return {int((t["t0"] - origin_s) // bar_s) for t in toks if t["t1"] - t["t0"] <= MAX_WORD_S and t["t0"] >= origin_s}


def span_bars(spec: dict, bpm: float, origin_s: float) -> tuple[int, int]:
    """First and last bar (0 at origin_s) a chop window covers."""
    bar_s = 240.0 / bpm
    return int((spec["start"] - origin_s) // bar_s), int((spec["end"] - origin_s) // bar_s)


TEMPLATE_SECTIONS = (("intro", 8), ("groove", 16), ("break", 8), ("build", 8), ("drop", 16), ("break", 8), ("build", 8), ("drop", 24), ("outro", 8))


_PC = {n: i for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())} | {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}


def _pc(r) -> int | None:
    return None if r is None else int(r) if not isinstance(r, str) else _PC[r]


def loop_roots(roots: list, loop: int = 8, tonic: int | None = None) -> list[int]:
    """The chord-root loop of a song: for each bar position in a loop of `loop` bars, the root heard most often at that position. `roots` is one pitch class or
    note name per bar (None for no note), as bassnotes.roots_per_bar returns. With `tonic` the loop is turned to start at its longest run of the tonic, since the
    first bar of the stem need not be the first bar of the progression. It is an estimate from a noisy bass line: the plan notes say to check it by ear.
    Raises ValueError when a position was never heard."""
    pcs = [_pc(r) for r in roots]
    out = []
    for p in range(loop):
        seen = [r for r in pcs[p::loop] if r is not None]
        if not seen:
            raise ValueError("no bass root heard at bar position %d of the %d bar loop" % (p, loop))
        out.append(max(sorted(set(seen)), key=seen.count))
    if tonic is not None and tonic in out:
        runs = []
        for p in range(loop):
            n = 0
            while n < loop and out[(p + n) % loop] == tonic:
                n += 1
            runs.append(n if out[(p - 1) % loop] != tonic or n == loop else 0)
        start = max(range(loop), key=lambda p: (runs[p], -p))
        out = out[start:] + out[:start]
    return out


def _air_ends(toks: list[dict], lo: float, hi: float, gap: float = 1.5) -> list[dict]:
    """Words that end between lo and hi seconds and are followed by at least `gap` seconds without a usable word: where a sung line stops."""
    good = [t for t in toks if t["t1"] - t["t0"] <= MAX_WORD_S]
    return [t for t, nxt in zip(good, good[1:] + [{"t0": 1e9}]) if lo <= t["t1"] <= hi and nxt["t0"] - t["t1"] >= gap]


def vocal_clips_for(toks: list[dict], hook_spec: dict, sections: list[dict], bpm: float, origin_s: float, max_s: float = 17.0) -> tuple[list[list], list[dict], str]:
    """The three long vocal clips of the remix: the chorus (from the pickup before the hook to the last line that ends in air within 16.5 s) in the first break,
    the first verse after it in the second break, and the chorus again in the last drop (4 s shorter). Returns (vocal_clips, clip_words, closer_word), the
    last being the word the chorus ends on. The windows are where to start; the cut is refined by ear and by Whisper later."""
    c0 = hook_spec["start"] - 0.9
    ends = _air_ends(toks, hook_spec["start"] + 8.0, hook_spec["start"] + 16.5)
    if not ends:
        raise ValueError("no sung line ends in air within 16.5 s of the hook at %.1f s" % hook_spec["start"])
    c1, closer = ends[-1]["t1"] + 0.1, ends[-1]["w"]
    starts = [t for t in toks if t["t0"] >= c1 + 0.5 and t["t1"] - t["t0"] <= MAX_WORD_S]
    v0 = starts[0]["t0"] - 0.05 if starts else c0
    vends = _air_ends(toks, v0 + 8.0, v0 + max_s)
    v1 = vends[-1]["t1"] + 0.1 if vends else v0 + max_s
    breaks = [s for s in sections if s["name"] == "break"]
    drops = [s for s in sections if s["name"] == "drop"]
    where = [breaks[0]["start"], breaks[-1]["start"], drops[-1]["start"]]
    bar_s = 240.0 / bpm
    spans = [(c0, c1, "Vocal chorus (break)"), (v0, v1, "Vocal verse (break 2)"), (c0, c1 - 4.0, "Vocal chorus (drop 2)")]
    clips = [[w, int(round((a - origin_s) / bar_s)), round(a, 2), round(b, 2), label, "phrase"] for w, (a, b, label) in zip(where, spans)]
    words = []
    for a, b, _l in spans:
        inside = [t["w"] for t in toks if a - 0.05 <= t["t0"] and t["t1"] <= b + 0.05 and t["t1"] - t["t0"] <= MAX_WORD_S]
        words.append({"head": " ".join(inside[:4]), "tail": " ".join(inside[-3:])})
    return clips, words, closer


def stretch_words(st: float) -> str:
    """The plan note on how the vocal's tempo moved (its pitch and formants never move)."""
    from . import stylepack
    if abs(st - 1) < 0.002:
        return "its own tempo"
    if st < 1:
        return ("%.1f%% slower than sung, pitch and formants kept (the person allows up to %.0f%%)" % (100 * (1 - st), 100 * (1 - stylepack.MAX_SLOWDOWN))
                if st >= stylepack.MAX_SLOWDOWN - 1e-9 else "slower than the person allows (%.0f%%): pick another tempo" % (100 * (1 - stylepack.MAX_SLOWDOWN)))
    if st <= stylepack.MAX_SPEEDUP:
        return "faster than sung, pitch and formants kept"
    return "faster than %.2fx: check by ear that it does not sound rushed" % stylepack.MAX_SPEEDUP


def draft_plan(name: str, toks: list[dict], *, source_bpm: float, key_pc: int, origin_s: float, roots: list | None = None, title: str = "", bpm: float | None = None,
               sections: tuple | None = None, style: str = "", arrangement: str = "", activity: list | None = None, roots_first_bar: int = -12,
               research: dict | None = None, midi: dict | None = None, every_part: bool = False, variety: dict | bool | None = None,
               mode: str = "") -> dict:
    """A song plan from the facts of one song. With a style the arrangement follows the song's own form (songform: full verses and choruses on
    the bar grid, the original's instrumentation, whole-phrase chops); arrangement "chops" keeps the older chop-led template. `activity` is the
    vocal stem's phrase spans (where nobody sings), `roots` the bass root per source bar from roots_first_bar, `research` the song notes from the
    web, `midi` an accepted reference MIDI ({"file", "fit", "qualities", "strum"}: the chord synth then plays the song's chords in its cadence).
    It is a draft for the person to review. Validate it with songplan.validate before use.

    variety (default on with a style): the song's own choices from the option bank (variety.choose): {"seed" (default the name), "lock"
    ({category: option id}), "history" (earlier remixes' choices, most recent first, so this one differs), "moods" and "energy" (the
    brief; the research notes' mood when not given), "surprise" (default true), "sounds" (parts that take a demo instrument)}; false keeps
    the style pack exactly as written. mode is the key's mode (major or minor) for scale-snapped arps."""
    from . import arrange, stylepack  # local: neither needs anything from here, but keep the import graph one way

    pack = stylepack.load(style) if style else None
    asked_bpm = bpm is not None
    bpm = float(bpm if bpm is not None else stylepack.pick_tempo(pack, source_bpm) if pack else 124.0)
    multiple = stylepack.vocal_multiple(bpm, source_bpm) if pack else 1.0
    picked_v = _variety(name, pack, variety, research, bpm, roots) if pack else None
    if picked_v:
        pack = picked_v["pack"]
        std = stylepack.standard_tempo(pack, source_bpm) if (pack.get("form") or {}).get("tempo") == "standard" and not asked_bpm else None
        if std:   # the form plays at the style's standard tempo (where its DJs play) rather than the least speed-up
            bpm, multiple = std, stylepack.vocal_multiple(std, source_bpm)
    if pack and (arrangement or "song") == "song" and not sections:
        plan = _song_form_plan(name, toks, pack, bpm, multiple, source_bpm, key_pc, origin_s, roots, roots_first_bar, title, activity, research, midi,
                               every_part=every_part, chop_mode=(picked_v or {}).get("chops", "games"))
        if plan is not None:
            _with_variety(plan, picked_v, int(key_pc), roots, mode)
            return plan
    sections = sections or (stylepack.sections_for(pack) if pack else TEMPLATE_SECTIONS)
    picked = plan_chops(toks, title=title)
    bars, secs = 0, []
    for label, n in sections:
        secs.append({"name": label, "start": bars, "end": bars + n})
        bars += n
    clips, clip_words, closer = vocal_clips_for(toks, picked["chops"]["hook"], secs, source_bpm, origin_s)
    roled = assign_roles(picked, closer_word=closer)
    notes = ["chord roots %s" % ("from the bass stem (an estimate: check it by ear)" if roots else "default: the tonic for eight bars"),
             "section map is the template, not the song's own", "chops and roles are a draft for review"]
    plan = {"name": name, "bpm": float(bpm), "source_bpm": float(source_bpm), "key_pc": int(key_pc), "origin_s": float(origin_s),
            "roots8": loop_roots(roots, tonic=int(key_pc)) if roots else [int(key_pc)] * 8, "sections": secs, "chops": picked["chops"], "echoed": roled["echoed"],
            "vocal_clips": clips, "clip_words": clip_words, "roles": roled["roles"], "notes": notes}
    plan["chop_events"] = [list(e) for e in arrange.arrange_chops(secs, roled["roles"])]
    plan["fx_cues"] = arrange.generate_fx_cues(secs)
    plan["pattern_bars"] = 16   # one piano roll per section, up to 16 bars (the person, 2026-10-29)
    _with_variety(plan, picked_v, int(key_pc), roots, mode)
    if pack:
        plan["style"], plan["vocal_multiple"] = pack["name"], multiple
        st = stylepack.stretch_of(bpm, multiple, source_bpm)
        plan["notes"].append("style %s at %g bpm; the vocal runs at x%g of the remix tempo (stretch x%.3f: %s)" % (
            pack["name"], bpm, multiple, st, stretch_words(st)))
    return plan


CHOP_SLOTS = {"games": None, "sparse": ("intro", "outro"), "stutter": ("intro", "stutter"), "none": ()}  # slot kinds each chop mode keeps


def _variety(name: str, pack: dict, opts, research: dict | None, bpm: float, roots) -> dict | None:
    """The variety choices for a draft, or None when switched off: {"result", "overrides", "pack" (the pack with them), "chops"}."""
    from . import variety
    if opts is False:
        return None
    o = dict(opts) if isinstance(opts, dict) else {}
    feel = o.get("moods") or (((research or {}).get("mood") or {}).get("feel") or [])
    brief = {"name": name, "style": pack["name"], "moods": feel, "energy": o.get("energy"), "bpm": bpm, "genres": o.get("genres") or [],
             "has_roots": bool(roots) and any(r is not None for r in roots), "sounds": o.get("sounds", 2)}
    res = variety.choose(brief, seed=o.get("seed", name), history=o.get("history"), lock=o.get("lock"), surprise=o.get("surprise", True) is not False)
    ov = variety.overrides(res)
    bank = variety.load_bank()
    chops = (variety.find(bank, res["choices"]["vocal"]).get("engine", {}).get("chops", "games")) if res["choices"].get("vocal") else "games"
    return {"result": res, "overrides": ov, "pack": variety.apply_overrides(pack, ov), "chops": chops, "brief": brief}


def _with_variety(plan: dict, picked: dict | None, key_pc: int, roots, mode: str) -> None:
    """Write the variety choices into the plan: what was chosen and why, the pack overrides, the production moves, the kit, the
    instruments, the FX cue policy, a harmony loop when the record gives no chords."""
    from . import arrange, variety
    if mode:
        plan["mode"] = mode
    if not picked:
        return
    res = picked["result"]
    plan["variety"] = {**res, "brief": {k: v for k, v in picked["brief"].items() if k != "name"}}
    plan["style_overrides"] = picked["overrides"]
    plan["production_overrides"] = variety.production_patch(res)
    kit = variety.kit(res)
    if kit:
        plan["kit"] = kit
    inst = variety.instruments(res)
    if inst:
        plan["instruments"] = inst
    policy = variety.fx_policy(res)
    if policy:
        plan["fx_cues"] = arrange.generate_fx_cues(plan["sections"], policy)
    has_roots = bool(roots) and any(r is not None for r in roots)
    reharm = variety.reharmonizes(res)
    loop = variety.harmony_loop(res, key_pc, mode=plan.get("mode", "")) if (reharm or not has_roots) else None
    if loop:
        plan["roots8"], plan["root_quality"] = loop[0], {str(k): v for k, v in loop[1].items()}
        splits = variety.harmony_splits(res, key_pc, mode=plan.get("mode", ""))
        if splits:
            plan["bar_splits8"] = splits
        if reharm:   # new chords under the whole vocal: the record's roots, and the reference file's chords built on them, step aside
            for k in ("bar_roots", "keys_notes", "midi"):
                plan.pop(k, None)
            plan.setdefault("notes", []).append("re-harmonized: the harmony loop plays under the whole song in place of the record's chords; "
                                                "check every vocal line against it by ear")
    lines = variety.describe(res)
    plan.setdefault("notes", []).append("variety (seed %s): %s" % (res.get("seed"), "; ".join(lines)))
    if plan.get("brief") is not None:
        plan["brief"]["decisions"] = lines
        plan["brief"]["surprise"] = res.get("surprise")


def _song_form_plan(name: str, toks: list[dict], pack: dict, bpm: float, multiple: float, source_bpm: float, key_pc: int, origin_s: float,
                    roots: list | None, roots_first_bar: int, title: str, activity: list | None, research: dict | None, midi: dict | None = None,
                    every_part: bool = False, chop_mode: str = "games") -> dict | None:
    """The song-form plan (see draft_plan), or None when the song shows no chorus (the chop template is used then)."""
    from . import arrange, songform, stylepack

    parts = songform.form(toks, title, origin_s, 240.0 / source_bpm, activity=activity)
    how = "the title line opens each chorus"
    if not any(p["kind"] == "chorus" for p in parts):  # the title is not sung at a chorus start: what the song sings again is the chorus
        parts = songform.form_by_repeats(toks, origin_s, 240.0 / source_bpm, activity=activity, title=title)
        how = "what the song sings again is chorus, what it sings once is verse (the title does not open a chorus)"
    chorus = next((p for p in parts if p["kind"] == "chorus"), None)
    if chorus is None:
        return None
    keep = {"verses": None, "choruses": None} if every_part else {}
    arr = songform.arrange(pack, parts, toks, origin_s=origin_s, bar_s=240.0 / source_bpm, **keep)
    chops = songform.phrase_chops(toks, chorus, title)
    if "hook" not in chops:
        return None
    stretch = stylepack.stretch_of(bpm, multiple, source_bpm)
    remix_bar_s = 240.0 / bpm
    keep_slots = CHOP_SLOTS.get(chop_mode)
    if keep_slots is not None:  # the vocal choice: fewer chop games (the singer carries the record)
        arr["slots"] = {k: (v if k in keep_slots else []) for k, v in arr["slots"].items()}
    events = songform.chop_games(arr["slots"], chops, lambda n: (chops[n]["end"] - chops[n]["start"]) / stretch / remix_bar_s)
    secs = arr["sections"]
    span = {p["bar0"]: p["bar1"] for p in parts}
    kept = ", ".join("%s %d to %d" % (c[4], c[1], span.get(c[1], c[1])) for c in arr["clips"] if c[6] == "vocals")
    notes = ["arrangement follows the song's own form (%s): " % how + ", ".join("%s %d..%d" % (p["kind"], p["bar0"], p["bar1"]) for p in parts),
             "kept whole: %s (source bars)" % kept,
             "chops are whole sung lines: " + "; ".join("%s (%d words, %.1f s)" % (k, len(v["words"].split()), v["end"] - v["start"]) for k, v in chops.items()),
             "chord roots %s" % ("follow the original's bass bar by bar where a remix bar carries a source bar" if roots else "default: the tonic"),
             "check by ear: the chorus and verse cuts, the chop phrases, the original instrumentation level"]
    st = stylepack.stretch_of(bpm, multiple, source_bpm)
    notes.append("style %s at %g bpm; the vocal runs at x%.3f of its own tempo (%s)" % (
        pack["name"], bpm, st, stretch_words(st)))
    if research:
        notes.append("research: %s" % "; ".join(str(f.get("what", f)) for f in research.get("favorites", [])[:4]))
        if research.get("mood"):
            feel = research["mood"].get("feel", [])
            fits = stylepack.for_mood(feel)
            notes.append("mood: %s; the style, palette and moves should match it (creative brief); packs that share the mood: %s" % (
                ", ".join(feel), ", ".join("%s (%s)" % (r["style"], ", ".join(r["matched"])) for r in fits) or "none yet"))
    plan = {"name": name, "bpm": float(bpm), "source_bpm": float(source_bpm), "key_pc": int(key_pc), "origin_s": float(origin_s),
            "roots8": loop_roots(roots, tonic=int(key_pc)) if roots and any(r is not None for r in roots) else [int(key_pc)] * 8,
            "sections": secs, "chops": chops, "echoed": [], "vocal_clips": arr["clips"], "clip_words": arr["clip_words"],
            "chop_events": events, "fx_cues": arrange.generate_fx_cues(secs), "notes": notes, "style": pack["name"], "vocal_multiple": multiple,
            "arrangement": "song", "form": parts, "brief": {"mood": (research or {}).get("mood"), "styles_for_mood": [r["style"] for r in stylepack.for_mood(((research or {}).get("mood") or {}).get("feel", []))], "decisions": [], "surprise": None}, "slots": {k: [list(x) if isinstance(x, (list, tuple)) else x for x in v] for k, v in arr["slots"].items()}}
    if "stutter" in chops and arr["slots"].get("stutter"):
        plan["stutter"] = {"chop": "stutter", "bars": list(arr["slots"]["stutter"]), "hits": [list(h) for h in songform.STUTTER_HITS]}
        carried = any(c[4].endswith("into the chorus") for c in arr["clips"])
        notes.append("the build before the last drop %sends on a %d-hit roll of '%s' in its last bar" % (
            "carries the verse on into the chorus's first lines and " if carried else "", len(songform.STUTTER_HITS), chops["stutter"]["words"]))
    if every_part:
        notes.append("every verse and every chorus is kept (a chorus sung straight after a chorus is its own drop, with no build between)")
    plan["pattern_bars"] = 16   # one piano roll per section, up to 16 bars, instead of a pattern a bar (the person, 2026-10-29)
    if roots:
        plan["bar_roots"] = songform.bar_roots(arr["src_bar"], roots, roots_first_bar, int(key_pc))
    if research:
        plan["research"] = research
    if midi and plan.get("bar_roots"):  # the reference file's chords and cadence on the record's own roots, replacing the style's chords
        plan["keys_notes"] = songform.keys_notes(secs, plan["bar_roots"], {int(k): v for k, v in midi["qualities"].items()}, midi["strum"], int(key_pc))
        plan["midi"] = {k: midi[k] for k in ("file", "fit", "qualities", "strum") if k in midi}
        plan["notes"].append("chords from the reference MIDI %s (roots agree on %.0f%% of %d bars): %s, strum %s; the chord synth plays them in the drops, "
                             "the second verse and the outro" % (Path(midi.get("file", "")).name, 100 * midi["fit"]["root_match"], midi["fit"]["bars_compared"],
                             ", ".join("%s %s" % ("C C# D D# E F F# G G# A A# B".split()[int(k)], v) for k, v in sorted(midi["qualities"].items(), key=lambda kv: int(kv[0]))
                                       if int(k) in set(plan["bar_roots"])), midi["strum"]))   # only chords the record's own roots play
    return plan
