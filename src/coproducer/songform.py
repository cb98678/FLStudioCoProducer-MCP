"""A song's own form from its vocal, and a remix arrangement that keeps it: full verses and full choruses on the bar grid, the original's
instrumentation where nobody sings, and vocal chops cut only as whole sung phrases.

Rules from the person (2026-10-25, changed 2026-10-28): the vocal plays at its own tempo, faster, or at most 6 % slower with its pitch kept
(stylepack.pick_tempo); chops are complete phrases in the song's natural language, never pieces of words and never cut before a final s;
lines stay whole and no word is ever cut, but which lines a remix keeps, in what order and in what role is the remix's choice (2026-10-28;
before, every verse and chorus whole and in order); some of the original's instrumentation, with cutting games only in between.

Method, on Whisper word times (which drift 0.2 to 0.7 s on singing, so every cut is snapped to the audio later by remixaudio):
- lines: words joined until a breath (a gap of BREATH_S or more);
- a chorus starts where the title's first content word is sung within three words after a breath (the tag line that ends a chorus sings the
  title mid-line, without the breath, and does not start one); on "Friends in Low Places" the hook word lands within 0.2 bar after bars 8,
  48, 64 and 96, which matches the song;
- vocal runs split where nobody sings for INSTRUMENTAL_S: those gaps are the intro, the solo and the outro;
- a run's part before its first chorus start is a verse; each chorus runs to the next chorus start or the end of its run, and a run of
  repeated choruses is split every 16 bars;
- bars: a part starts on the bar its first stressed word falls in (start_bar), so a pickup sung before the bar line stays with its part.
"""
from __future__ import annotations

import math
import re

from .songanalysis import MAX_WORD_S, STOP

BREATH_S = 0.25
INSTRUMENTAL_S = 3.0
CHORUS_SPLIT_BARS = 16
PHRASE_S = (0.8, 4.5)  # a chop is one sung phrase of this length
HOOK_MAX_S = 12.0  # the hook chop: the title line and the line sung straight after it (the person's own hook on Friends: 11 s, two lines)
PICKUPS = {"cause", "cuz", "cos", "and", "but", "so", "oh", "well", "now", "then", "yeah", "hey"}  # a pickup slurred from the note before is left off a chop
# The roll into the last drop, as the person cut it by hand on the techno remix (2026-10-26): one syllable of the hook replayed in the build's
# last bar, each hit shorter and sooner: (start, length) in bars.
STUTTER_HITS = ((0.0, 0.25), (0.25, 0.234), (0.5, 0.156), (0.6875, 0.094), (0.8125, 0.0625), (0.890625, 0.0625), (0.953125, 0.047))
NOTE_PC = {n: i for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())} | {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}
MAJOR, MINOR = (0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 8, 10)


def good(toks: list[dict]) -> list[dict]:
    """Word records with a plausible time (Whisper gives some invented or overlapping words), in time order."""
    out = [t for t in toks if 0.03 <= t["t1"] - t["t0"] <= MAX_WORD_S]
    out.sort(key=lambda t: t["t0"])
    return [t for i, t in enumerate(out) if i == 0 or t["t0"] >= out[i - 1]["t0"]]


def gap_before(toks: list[dict], i: int) -> float:
    return toks[i]["t0"] - toks[i - 1]["t1"] if i > 0 else 99.0


def lines(toks: list[dict], breath_s: float = BREATH_S) -> list[dict]:
    """Sung lines: [{"i0", "i1" (exclusive), "t0", "t1", "words"}], split at every breath."""
    out, i0 = [], 0
    for i in range(1, len(toks) + 1):
        if i == len(toks) or gap_before(toks, i) >= breath_s:
            seg = toks[i0:i]
            out.append({"i0": i0, "i1": i, "t0": seg[0]["t0"], "t1": seg[-1]["t1"], "words": [t["w"] for t in seg]})
            i0 = i
    return out


def bar_pos(t: float, origin_s: float, bar_s: float) -> float:
    return (t - origin_s) / bar_s


def start_bar(t: float, origin_s: float, bar_s: float, pickup: float = 0.3) -> int:
    """The bar a part sung from t belongs to: a word up to 0.7 bar before a bar line is a pickup into it."""
    return math.ceil(bar_pos(t, origin_s, bar_s) - pickup)


def end_bar(t: float, origin_s: float, bar_s: float, hold: float = 0.15) -> int:
    """The bar line a part sung until t ends on: a held last note up to 0.15 bar past a bar line still ends there."""
    return math.ceil(bar_pos(t, origin_s, bar_s) - hold)


def title_words(title: str) -> list[str]:
    return [w for w in re.findall(r"[a-z']+", (title or "").lower()) if w not in STOP]


def chorus_starts(toks: list[dict], title: str, breath_s: float = BREATH_S) -> list[dict]:
    """[{"hook" (token index of the title's first content word), "line" (index of the first word of its line)}] where a chorus starts: the
    title's first content word, with another title word in the next four, sung within three words after a breath."""
    want = title_words(title)
    if len(want) < 2:
        return []
    out = []
    for i, t in enumerate(toks):
        if t["w"] != want[0] or not set(want[1:]) & {x["w"] for x in toks[i + 1 : i + 5]}:
            continue
        j = i
        while j > 0 and i - j < 3 and gap_before(toks, j) < breath_s:
            j -= 1
        if gap_before(toks, j) >= breath_s:
            out.append({"hook": i, "line": j})
    return out


def vocal_runs(spans: list, gap_s: float = INSTRUMENTAL_S) -> list[tuple[float, float]]:
    """Stretches of singing from audio phrase spans [(t0, t1)] (vocalchops.phrases on the vocal stem), joined across gaps under gap_s."""
    out: list[list[float]] = []
    for t0, t1 in sorted((float(a), float(b)) for a, b in spans):
        if out and t0 - out[-1][1] < gap_s:
            out[-1][1] = max(out[-1][1], t1)
        else:
            out.append([t0, t1])
    return [(a, b) for a, b in out]


def _round_len(bar0: int, bar1: int) -> int:
    """A part's end bar with its length rounded to a multiple of 4 when it is one bar short or long of one (15 bars of chorus is 16)."""
    n = bar1 - bar0
    r = n % 4
    return bar1 + 1 if r == 3 and n >= 3 else bar1 - 1 if r == 1 and n > 4 else bar1


def form(toks: list[dict], title: str, origin_s: float, bar_s: float, song_start_s: float = 0.0, activity: list | None = None) -> list[dict]:
    """The song's parts in order: [{"kind": intro | verse | chorus | instrumental, "bar0", "bar1", "t0", "t1", "i0", "i1"}]. Bars count from
    origin_s (parts before it have negative bars). Where nobody sings comes from `activity`, the vocal stem's own phrase spans, when given
    (Whisper drops words, so its gaps invent breaks inside a chorus); else from gaps between words. A chorus repeats every L bars, L the
    length of the first one: later chorus starts must fall on that spacing (the tag line that ends a chorus sings the title 12 bars in).
    t0 and t1 are the first sung onset and the last word's end for sung parts, the bar lines for instrumental ones; i0 and i1 index the words."""
    toks = good(toks)
    if not toks:
        return []
    runs = vocal_runs(activity) if activity else vocal_runs([(t["t0"], t["t1"]) for t in toks])
    cands = sorted({start_bar(toks[c["hook"]]["t0"], origin_s, bar_s): c for c in chorus_starts(toks, title)}.items())
    parts: list[dict] = []
    lead = math.floor(bar_pos(song_start_s, origin_s, bar_s) + 0.5)
    chorus_len = 0
    for t0, t1 in runs:
        idx = [i for i, t in enumerate(toks) if t0 - 0.3 <= t["t0"] <= t1 + 0.1]
        if not idx:
            continue
        bar_a = start_bar(t0, origin_s, bar_s)
        prev_end = parts[-1]["bar1"] if parts else lead
        if bar_a - prev_end >= 2:
            parts.append(_inst("intro" if not parts else "instrumental", prev_end, bar_a, origin_s, bar_s))
        bar_a = max(bar_a, prev_end)
        cuts, last = [(idx[0], bar_a, "verse", t0)], None
        for bar, c in cands:
            if not idx[0] <= c["line"] <= idx[-1] or bar <= bar_a - 1:
                continue
            if last is not None and chorus_len and not (bar - last >= chorus_len - 1 and (bar - last) % chorus_len in (0, 1, chorus_len - 1)):
                continue  # a tag line inside a chorus, not a new one
            if last is not None and chorus_len:  # choruses keep their length: a start one bar off is word-time drift (Whisper's window edges)
                bar = last + round((bar - last) / chorus_len) * chorus_len
            cuts.append((c["line"], max(bar, bar_a), "chorus", toks[c["line"]]["t0"]))
            last = bar
        if len(cuts) > 1 and cuts[1][1] <= bar_a:  # the run opens on a chorus
            cuts = [(cuts[1][0], bar_a, "chorus", t0)] + cuts[2:]
        end = _round_len(cuts[-1][1], max(end_bar(t1, origin_s, bar_s), cuts[-1][1] + 1))
        for k, (ia, bar0, kind, start_t) in enumerate(cuts):
            ib, bar1 = (cuts[k + 1][0], cuts[k + 1][1]) if k + 1 < len(cuts) else (idx[-1] + 1, end)
            if bar1 <= bar0 or ib <= ia:
                continue
            p = {"kind": kind, "bar0": bar0, "bar1": bar1, "t0": round(start_t, 3), "t1": round(min(toks[ib - 1]["t1"], t1 if k + 1 == len(cuts) else 1e9), 3), "i0": ia, "i1": ib}
            if k + 1 == len(cuts):
                p["t1"] = round(t1, 3)  # the run's last part ends where the voice stops in the audio
            if kind == "chorus" and not chorus_len:
                chorus_len = max(8, _round_len(bar0, bar1) - bar0) if k + 1 == len(cuts) else max(8, bar1 - bar0)
                chorus_len = int(round(chorus_len / 4.0) * 4)
            parts += _split_chorus(p, toks, origin_s, bar_s, chorus_len or CHORUS_SPLIT_BARS)
    return parts


REPEAT_N = 4        # content words in a run that counts as sung again (3 took a verse callback, "gift ... one liners", for a chorus)
REPEAT_GAP_S = 8.0  # the other time it is sung must be this far away (a line sung twice in a row inside one part is not a chorus)
SMOOTH_BARS = 4     # a run of one kind shorter than this many bars, between two of the other (or at the edge of a run), takes their kind


def repeated_words(toks: list[dict], n: int = REPEAT_N, gap_s: float = REPEAT_GAP_S) -> list[bool]:
    """Per word: is it inside a run of n content words that the song sings again at least gap_s away (chorus material), or not (verse)."""
    content = [i for i, t in enumerate(toks) if t["w"] not in STOP]
    seq = [toks[i]["w"] for i in content]
    occ: dict = {}
    for k in range(len(seq) - n + 1):
        occ.setdefault(tuple(seq[k:k + n]), []).append(k)
    rep = [False] * len(toks)
    for ks in occ.values():
        if len(ks) < 2:
            continue
        for k in ks:
            if any(abs(toks[content[k]]["t0"] - toks[content[j]]["t0"]) >= gap_s for j in ks):
                for m in range(k, k + n):
                    rep[content[m]] = True
    last = False
    for i, t in enumerate(toks):  # a little word takes the kind of the content word before it
        if t["w"] in STOP:
            rep[i] = last
        else:
            last = rep[i]
    return rep


def title_lines(toks: list[dict], title: str) -> list[bool]:
    """Per word: is it in a line that ends on the title, when the title is one word the song ends at least three lines on ("Girls": the
    hook lines all end on it). A one-word title cannot open a chorus the way chorus_starts needs, but the lines it closes are the chorus."""
    want = title_words(title)
    out = [False] * len(toks)
    if len(want) != 1:
        return out
    ends = [ln for ln in lines(toks) if ln["words"] and ln["words"][-1].rstrip("s") == want[0].rstrip("s")]
    if len(ends) < 3:
        return out
    for ln in ends:
        for i in range(ln["i0"], ln["i1"]):
            out[i] = True
    return out


def form_by_repeats(toks: list[dict], origin_s: float, bar_s: float, song_start_s: float = 0.0, activity: list | None = None,
                    title: str = "") -> list[dict]:
    """The song's parts when its title does not open a chorus (\"The Curse of Curves\" sings its title only at the end of a section): what the
    song sings again is chorus, what it sings once is verse (a bridge reads as a verse). Runs shorter than SMOOTH_BARS between two of the
    other kind join them (a tagline the recogniser heard differently each time stays inside its chorus); instrumental gaps come from the vocal stem as in form(). Same part records as form()."""
    toks = good(toks)
    if not toks:
        return []
    rep = [a or b for a, b in zip(repeated_words(toks), title_lines(toks, title))]
    runs = vocal_runs(activity) if activity else vocal_runs([(t["t0"], t["t1"]) for t in toks])
    parts: list[dict] = []
    lead = math.floor(bar_pos(song_start_s, origin_s, bar_s) + 0.5)
    for t0, t1 in runs:
        idx = [i for i, t in enumerate(toks) if t0 - 0.3 <= t["t0"] <= t1 + 0.1]
        if not idx:
            continue
        segs: list[list] = []  # [kind, first word, last word]
        for i in idx:
            kind = "chorus" if rep[i] else "verse"
            if segs and segs[-1][0] == kind:
                segs[-1][2] = i
            else:
                segs.append([kind, i, i])
        changed = True
        while changed and len(segs) > 1:  # smooth: a short run between two of the other kind joins them
            changed = False
            for k in range(len(segs)):
                a, b = segs[k][1], segs[k][2]
                if toks[b]["t1"] - toks[a]["t0"] < SMOOTH_BARS * bar_s and (k == 0 or k == len(segs) - 1 or segs[k - 1][0] == segs[k + 1][0]):
                    other = segs[k + 1] if k == 0 else segs[k - 1]
                    other[1], other[2] = min(other[1], a), max(other[2], b)
                    segs.pop(k)
                    changed = True
                    break
            merged = []
            for sg in segs:
                if merged and merged[-1][0] == sg[0]:
                    merged[-1][2] = sg[2]
                else:
                    merged.append(sg)
            segs = merged
        for k in range(len(segs) - 1):  # a part changes at a breath when there is one within four words ("...curse of curves" | "so with...")
            b = segs[k + 1][1]
            near = [j for j in range(max(segs[k][1] + 1, b - 4), min(segs[k + 1][2], b + 4) + 1) if gap_before(toks, j) >= BREATH_S]
            if near:
                j = min(near, key=lambda j: abs(j - b))
                segs[k][2], segs[k + 1][1] = j - 1, j
        for k in range(len(segs) - 1):  # a little word sung straight into the next part is its pickup ("the" of "the inside lingo")
            while (segs[k][2] > segs[k][1] and toks[segs[k][2]]["w"].replace("'", "") in PICKUPS | {"the", "a", "an"}
                   and gap_before(toks, segs[k][2] + 1) < BREATH_S and segs[k + 1][1] - segs[k][2] <= 2):
                segs[k][2] -= 1
                segs[k + 1][1] -= 1
        bar_a = start_bar(t0, origin_s, bar_s)
        prev_end = parts[-1]["bar1"] if parts else lead
        if bar_a - prev_end >= 2:
            parts.append(_inst("intro" if not parts else "instrumental", prev_end, bar_a, origin_s, bar_s))
        bars = [max(bar_a, prev_end) if k == 0 else start_bar(toks[sg[1]]["t0"], origin_s, bar_s) for k, sg in enumerate(segs)]
        end = _round_len(bars[-1], max(end_bar(t1, origin_s, bar_s), bars[-1] + 1))
        for k, sg in enumerate(segs):
            bar0, bar1 = bars[k], bars[k + 1] if k + 1 < len(segs) else end
            if bar1 <= bar0:
                continue
            p = {"kind": sg[0], "bar0": bar0, "bar1": bar1, "t0": round(t0 if k == 0 else toks[sg[1]]["t0"], 3),
                 "t1": round(t1 if k + 1 == len(segs) else toks[sg[2]]["t1"], 3), "i0": sg[1], "i1": sg[2] + 1}
            parts.append(p)
    return parts


def _inst(kind: str, bar0: int, bar1: int, origin_s: float, bar_s: float) -> dict:
    return {"kind": kind, "bar0": bar0, "bar1": bar1, "t0": round(origin_s + bar0 * bar_s, 3), "t1": round(origin_s + bar1 * bar_s, 3), "i0": None, "i1": None}


def _split_chorus(p: dict, toks: list[dict], origin_s: float, bar_s: float, length: int = CHORUS_SPLIT_BARS) -> list[dict]:
    """A chorus part longer than one and a half choruses is repeated choruses the hook test missed: split it every `length` bars."""
    if p["kind"] != "chorus" or p["bar1"] - p["bar0"] < length * 1.5:
        return [p]
    out, b = [], p["bar0"]
    while b < p["bar1"]:
        e = min(b + length, p["bar1"])
        if p["bar1"] - e < 4:  # a remnant under 4 bars (the next chorus came in a bar late) stays with this chorus, never a part of its own
            e = p["bar1"]
        lo, hi = origin_s + b * bar_s - 0.7 * bar_s, origin_s + e * bar_s - 0.7 * bar_s
        idx = [i for i in range(p["i0"], p["i1"]) if lo <= toks[i]["t0"] < hi or (b == p["bar0"] and toks[i]["t0"] < hi)]
        if idx:
            first = b == p["bar0"]  # the first piece keeps the part's own start and its pickup
            out.append({"kind": "chorus", "bar0": b, "bar1": e, "t0": p["t0"] if first else toks[idx[0]]["t0"], "t1": toks[idx[-1]]["t1"],
                        "i0": p["i0"] if first else idx[0], "i1": idx[-1] + 1})
        b = e
    return out


def scale_roots(roots_per_bar: list, key_pc: int, mode: str = "major") -> list:
    """Bass roots per source bar with notes outside the key replaced by the bar before (a passing note is not the chord). Names or numbers in."""
    steps = MAJOR if mode != "minor" else MINOR
    keep = {(key_pc + s) % 12 for s in steps}
    out, prev = [], None
    for r in roots_per_bar:
        pc = None if r is None else (NOTE_PC[r] if isinstance(r, str) else int(r))
        pc = pc if pc in keep else prev
        out.append(pc)
        prev = pc if pc is not None else prev
    return out


def _len4(n: int, least: int = 4) -> int:
    return max(least, int(math.ceil(n / 4.0) * 4))


def arrange(pack: dict, parts: list[dict], toks: list[dict], verses: int | None = 2, choruses: int | None = 2, orig_verses: int = 1,
            origin_s: float | None = None, bar_s: float | None = None) -> dict:
    """Remix sections from the song's own form: the pack's intro (the song's instrumental intro at its end), then the song in order with every
    verse a groove of its own length, every chorus a drop (after the pack's build) that plays the whole chorus and then eight bars of chop
    games, every instrumental part between them a break that plays the original's instrumentation, and the pack's outro. The first `verses`
    verses and `choruses` choruses are kept (None: all of them). A chorus sung straight after a chorus is a drop of its own with no build
    and no games between. With origin_s and bar_s, the build before the last drop carries the verse on (the person's edit, 2026-10-26: the
    chorus's first lines sung over the build, through the last whole line before its last bar, which holds the stutter roll), and the drop
    then plays the chorus from its start. Returns {"sections", "clips" [remix_bar, orig_bar, t0, t1, label, mode, stem], "clip_words",
    "src_bar" (the source bar each remix bar plays, None in builds, intro and outro), "slots" (where chop games go; "stutter" the bar of the
    roll)}.

    pack["form"] (a form option from the variety bank) changes the shape: build ("always", "alternate", "last" or "never": which choruses
    get a build before them), tail_bars (the chop games after a chorus, 8 by default, 0 for none), bridge and bridge_bars (a breakdown
    before the last chorus), labels ({kind: marker name}); the pack's sections give the intro, build and outro lengths as before.

    The form can also turn a part's function from pass to pass (Freejak's Sorry remix, 2026-10-28): verse_as and chorus_as list the
    section kind for the first, second... verse and chorus (the last entry repeats; default groove and drop). A verse "break" is sung over
    the break's parts (the bass out). A chorus "break" is sung over a break with no build before it, then drop_after bars (16 by default)
    of drop follow it with the chop games (the hook) and no vocal line of its own. tail_break puts that many bars of break between a
    chorus sung on a drop and its chop-game tail (a short breath before the last hook drop)."""
    toks = good(toks)
    form = pack.get("form") or {}
    policy = form.get("build", "always")
    tail = int(form.get("tail_bars", 8))
    verse_as, chorus_as = list(form.get("verse_as") or ["groove"]), list(form.get("chorus_as") or ["drop"])
    drop_after, tail_break = int(form.get("drop_after", 16)), int(form.get("tail_break", 0))

    def role(roles: list, n: int) -> str:
        return roles[min(n, len(roles) - 1)]
    labels = form.get("labels") or {}
    plen = {}
    for kind, n in pack["sections"]:
        plen.setdefault(kind, int(n))
    secs, clips, words, src = [], [], [], []
    slots: dict = {"intro": [], "build": [], "answer": [], "tail": [], "outro": [], "stutter": []}

    def add(name: str, n: int, src0: int | None = None, loop: int = 0) -> int:
        b = secs[-1]["end"] if secs else 0
        secs.append({"name": name, "start": b, "end": b + n})
        if labels.get(name):
            secs[-1]["label"] = labels[name]
        src.extend([None if src0 is None else src0 + (k % loop if loop else k) for k in range(n)])
        return b

    def clip(remix_bar: int, p: dict, label: str, stem: str, nxt: dict | None) -> None:
        if stem == "other":
            clips.append([remix_bar, p["bar0"], p["t0"] if p["kind"] != "intro" else round(max(0.0, p["t0"] - 0.0), 3), p["t1"], label, "bars", "other"])
            words.append({"head": "", "tail": ""})
            return
        joined = nxt is not None and nxt.get("i0") is not None and nxt["t0"] - p["t1"] < 0.5  # the next part is sung straight on: stop before its first word
        clips.append([remix_bar, p["bar0"], round(p["t0"], 3), round(nxt["t0"] if joined else p["t1"], 3), label, "word" if joined else "phrase", "vocals"])
        w = [t["w"] for t in toks[p["i0"]:p["i1"]]]
        row = {"head": " ".join(w[:4]), "tail": " ".join(w[-3:]), "head_t1": round(toks[p["i0"]]["t1"], 3)}
        k = nxt["i0"] if nxt is not None and nxt.get("i0") is not None else p["i1"]
        if k < len(toks):  # the next sung word: no cut end may run into it (a legato line has no gap to stop at)
            row["next_t0"], row["next_t1"] = round(nxt["t0"] if k == (nxt or {}).get("i0") else toks[k]["t0"], 3), round(toks[k]["t1"], 3)
            row["next_w"] = toks[k]["w"]
        words.append(row)

    def carry_on(n_clip: int, until_bar: int) -> bool:
        """Let vocal clip n_clip run on in the source until the last whole line that ends before remix bar until_bar."""
        c = clips[n_clip]
        t_end = origin_s + (c[1] + (until_bar - c[0])) * bar_s
        ends = [k for k, t in enumerate(toks) if t["t0"] >= c[3] - 0.05 and t["t1"] <= t_end - 0.1
                and (k + 1 == len(toks) or gap_before(toks, k + 1) >= BREATH_S)]   # the last phrase end (a breath after it) before that bar
        if not ends:
            return False
        k = ends[-1]
        c[3], c[5] = round(toks[k]["t1"], 3), "phrase"
        c[4] += " into the chorus"
        row = words[n_clip]
        row["tail"] = " ".join(t["w"] for t in toks[max(0, k - 2):k + 1])
        row.pop("next_t0", None)
        row.pop("next_t1", None)
        row.pop("next_w", None)
        if k + 1 < len(toks):
            row["next_t0"], row["next_t1"], row["next_w"] = round(toks[k + 1]["t0"], 3), round(toks[k + 1]["t1"], 3), toks[k + 1]["w"]
        return True

    order = [p for p in parts if p["kind"] != "intro"]
    intro = next((p for p in parts if p["kind"] == "intro"), None)
    n_intro = plen.get("intro", 16)
    add("intro", n_intro)
    if intro and intro["bar1"] - intro["bar0"] <= n_intro:
        clip(n_intro - (intro["bar1"] - intro["bar0"]), intro, "Original intro", "other", None)
    slots["intro"].append((secs[-1]["start"], secs[-1]["end"]))
    n_ch = sum(1 for q in order if q["kind"] == "chorus")
    n_v = sum(1 for q in order if q["kind"] == "verse")
    keep_c = n_ch if choruses is None else min(choruses, n_ch)
    keep_v = n_v if verses is None else min(verses, n_v)
    # Which builds carry the verse on: the last, and every second one counting back from it (the person carried the last build on Friends,
    # the first and last of three on The Curse of Curves, and left the others to the chop games, 2026-10-26).
    kinds, uv, uc = [], 0, 0
    for p in order:
        if p["kind"] == "verse" and uv < keep_v:
            kinds.append("verse")
            uv += 1
        elif p["kind"] == "instrumental" and uc and uc < keep_c:
            kinds.append("instrumental")
        elif p["kind"] == "chorus" and uc < keep_c:
            kinds.append("chorus")
            uc += 1
    starts = [k for k, kind in enumerate(kinds) if kind == "chorus" and (k == 0 or kinds[k - 1] != "chorus")]
    carry_builds = {n for n in range(len(starts)) if (len(starts) - 1 - n) % 2 == 0}
    n_build = 0
    used_v = used_c = 0
    verse_clip = None
    for i, p in enumerate(order):
        nxt = order[i + 1] if i + 1 < len(order) else None
        n = p["bar1"] - p["bar0"]
        if p["kind"] == "verse" and used_v < keep_v:
            b = add(role(verse_as, used_v), _len4(n, 8), p["bar0"])
            clip(b, p, "Verse %d" % (used_v + 1), "vocals", nxt)
            verse_clip = len(clips) - 1
            if used_v < orig_verses:  # the original's guitars under the first verse; later verses get the synth version (no doubling)
                clip(b, p, "Original verse %d" % (used_v + 1), "other", None)
            used_v += 1
        elif p["kind"] == "instrumental" and used_c and used_c < keep_c:
            b = add("break", _len4(n), p["bar0"])
            clip(b, p, "Original solo" if n >= 4 else "Original break", "other", None)
            verse_clip = None
        elif p["kind"] == "chorus" and used_c < keep_c and role(chorus_as, used_c) == "break":
            core = _len4(n, 8)
            b = add("break", core, p["bar0"], loop=core)       # the chorus sung over the break: the lift, no build before it
            clip(b, p, "Chorus %d (break)" % (used_c + 1), "vocals", nxt)
            verse_clip = None
            if drop_after:
                d = add("drop", drop_after, p["bar0"], loop=core)   # the drop it lifts into: the hook games, the chorus's chords
                slots["tail"].append((d, d + drop_after))
            n_build += 1
            used_c += 1
        elif p["kind"] == "chorus" and used_c < keep_c:
            back_to_back = bool(secs) and secs[-1]["name"] == "drop"
            if form.get("bridge") and not back_to_back and n_build == len(starts) - 1 and len(starts) > 1 and secs[-1]["name"] != "break":
                add("break", int(form.get("bridge_bars", 8)))   # a breakdown before the last chorus (the bridge or Mid 8)
                verse_clip = None
            if not back_to_back and secs[-1]["name"] != "build" and not _wants_build(policy, n_build, len(starts)):
                n_build += 1   # this chorus comes in straight from the verse (a pop lift, not a riser build)
            elif not back_to_back and secs[-1]["name"] != "build":
                after_verse = secs[-1]["name"] == "groove" and verse_clip is not None
                b = add("build", plen.get("build", 8))
                end = secs[-1]["end"]
                last_build = n_build == len(starts) - 1
                can = after_verse and n_build in carry_builds and origin_s is not None and bar_s is not None
                if can and last_build and carry_on(verse_clip, end - 1):
                    slots["stutter"].append(end - 1)  # sung on to the last bar, then the roll
                elif can and not last_build and carry_on(verse_clip, b + (end - b) // 2):
                    slots["answer"].append((b, end))  # sung on through its first half, then the line answers into the drop
                elif last_build:
                    slots["build"].append((b, end - 1))  # the games, then the roll in the last bar (no verse to carry on here)
                    slots["stutter"].append(end - 1)
                else:
                    slots["build"].append((b, end))
                n_build += 1
            verse_clip = None
            core = _len4(n, 8)
            more = nxt is not None and nxt["kind"] == "chorus" and used_c + 1 < keep_c  # the song sings the next chorus straight on
            if tail_break and not more and tail:
                b = add("drop", core, p["bar0"], loop=core)
                clip(b, p, "Chorus %d" % (used_c + 1), "vocals", nxt)
                add("break", tail_break)
                t0 = add("drop", tail, p["bar0"], loop=core)
                slots["tail"].append((t0, t0 + tail))
            else:
                b = add("drop", core + (0 if more else tail), p["bar0"], loop=core)
                clip(b, p, "Chorus %d" % (used_c + 1), "vocals", nxt)
                if not more and tail:
                    slots["tail"].append((b + core, b + core + tail))
            used_c += 1
        if used_c >= keep_c and used_v >= keep_v:
            break
    b = add("outro", plen.get("outro", 16))
    slots["outro"].append((b, secs[-1]["end"]))
    return {"sections": secs, "clips": clips, "clip_words": words, "src_bar": src, "slots": slots}


def _wants_build(policy: str, n: int, total: int) -> bool:
    """Whether the n-th chorus start (of total) gets a build: every one, every other one counting back from the last, the last only, none."""
    if policy == "never":
        return False
    if policy == "last":
        return n == total - 1
    if policy == "alternate":
        return (total - 1 - n) % 2 == 0
    return True


def phrase_chops(toks: list[dict], chorus: dict, title: str) -> dict:
    """Chops that are whole sung phrases from one chorus: the hook (from its line's first word through the title's last word and on through
    the line sung straight after it, the couplet, while that stays within HOOK_MAX_S; the person re-cut the Friends hook that way, 2026-10-26),
    the chorus's other complete lines of PHRASE_S seconds, most repeated in the song first, and "stutter", one syllable of the hook (its first
    title word) for the roll into the last drop. Each spec: start, end (the last word's end), end_mode (phrase when air follows, else word:
    the cut stops at the next word's onset), words, next and next_t0; "after_pickup" is the second word's start when the first is a pickup
    word (remixaudio leaves it off when it is slurred from the note before, as the person did with "'cause")."""
    toks = good(toks)
    seg = toks[chorus["i0"]:chorus["i1"]]
    off = chorus["i0"]
    want = title_words(title)
    found = [c for c in chorus_starts(toks, title) if chorus["i0"] <= c["line"] < chorus["i1"]]
    out: dict = {}
    hook_span = None
    if not (found and want):  # the title is not sung at a line start: the chorus line the song sings most is the hook
        counts = {}
        for ln in lines(toks):
            counts.setdefault(tuple(w for w in ln["words"] if w not in STOP), []).append(ln)
        best = max(lines(seg), key=lambda ln: (len(counts.get(tuple(w for w in ln["words"] if w not in STOP), [])) if len(ln["words"]) >= 4 else 0,
                                                -ln["t0"]), default=None)
        if best is not None:
            found = [{"line": best["i0"] + off, "hook": best["i0"] + off}]
            want = [toks[best["i1"] - 1 + off]["w"]]
    if found and want:
        a = found[0]["line"]
        z = next((k for k in range(found[0]["hook"], min(found[0]["hook"] + 30, len(toks))) if toks[k]["w"] == want[-1]), found[0]["hook"])
        k = z + 1                                   # the couplet: on through the next line when it is sung straight on
        if k < len(toks) and gap_before(toks, k) < 0.8:
            j = k
            while j + 1 < len(toks) and gap_before(toks, j + 1) < BREATH_S:
                j += 1
            if toks[j]["t1"] - toks[a]["t0"] <= HOOK_MAX_S:
                z = j
        out["hook"] = _spec(toks, a, z + 1)
        if toks[a]["w"].replace("'", "") in PICKUPS and a + 1 <= z:
            out["hook"]["after_pickup"], out["hook"]["after_pickup_t1"] = round(toks[a + 1]["t0"], 2), round(toks[a + 1]["t1"], 2)
        hook_span = (a, z + 1)
        tw = next((i for i in range(found[0]["hook"], z + 1) if toks[i]["w"] in title_words(title) and 0.2 <= toks[i]["t1"] - toks[i]["t0"] <= 0.9),
                  next((i for i in range(found[0]["hook"], z + 1) if toks[i]["w"] not in STOP and 0.2 <= toks[i]["t1"] - toks[i]["t0"] <= 0.9), None))
        if tw is not None:
            st = _spec(toks, tw, tw + 1)
            st["end_mode"] = "word"
            if "next_t0" in st:
                st["end"] = st["next_t0"]
            out["_stutter"] = st
    keys = {}
    for ln in lines(toks):
        keys.setdefault(tuple(w for w in ln["words"] if w not in STOP), []).append(ln)
    cands = []
    for ln in lines(seg):
        n0, n1 = ln["i0"] + off, ln["i1"] + off
        dur = toks[n1 - 1]["t1"] - toks[n0]["t0"]
        key = tuple(w for w in ln["words"] if w not in STOP)
        inside = hook_span is not None and n0 < hook_span[1] and n1 > hook_span[0]
        if PHRASE_S[0] <= dur <= PHRASE_S[1] and key and not inside:
            cands.append((-len(keys.get(key, [])), toks[n0]["t0"], n0, n1))
    for k, (_r, _t, n0, n1) in enumerate(sorted(cands)[:3]):
        out["line%d" % (k + 1)] = _spec(toks, n0, n1)
    if "_stutter" in out:
        out["stutter"] = out.pop("_stutter")   # last, so the games take the hook and the first line
    for v in out.values():
        v.pop("_i0", None)
    return out


def _spec(toks: list[dict], a: int, z: int) -> dict:
    nxt = toks[z] if z < len(toks) else None
    air = nxt is None or nxt["t0"] - toks[z - 1]["t1"] >= BREATH_S
    spec = {"start": round(toks[a]["t0"], 2), "end": round(toks[z - 1]["t1"], 2), "end_mode": "phrase" if air else "word",
            "words": " ".join(t["w"] for t in toks[a:z]), "first_t1": round(toks[a]["t1"], 2), "_i0": a}   # first_t1: cutrefine.word_start
    if nxt is not None:
        spec["next"], spec["next_t0"], spec["next_t1"] = nxt["w"], round(nxt["t0"], 2), round(nxt["t1"], 2)
        if not air:
            spec["end"] = round(nxt["t0"], 2)  # the cut stops at the next word's onset (snap_end "word" finds it in the audio)
    return spec


def chop_games(slots: dict, chops: dict, bars_of=lambda name: 1.0) -> list[list]:
    """(bar, step, chop, velocity, key) rows: whole phrases only, each placed after the last one has finished (bars_of(name) is a chop's length
    in remix bars; the next one starts on the even bar after it). The intro teases the hook halfway; a build trades a line and the hook, a
    semitone higher each time; a drop's last bars answer the chorus with the hook and a line; the outro closes on a line and the hook."""
    hook = "hook" if "hook" in chops else next(iter(chops))
    line = next((k for k in chops if k not in (hook, "stutter")), hook)
    e: list[list] = []

    def run(a: int, z: float, names: tuple, vel: int, climb: bool) -> None:
        b, k = a, 0
        while b < z:
            name = names[k % len(names)]
            if b + bars_of(name) > z + 0.1:  # it would ring into the next section
                break
            up = False  # every chop stays in the song's key (the person took a line pitched up a step back to its key, 2026-10-26)
            e.append([b, 0, name, min(127, vel + (6 * k if climb else 0)), 60 + (k if up else 0)])
            b += max(2, 2 * math.ceil(bars_of(name) / 2.0))
            k += 1
    for a, z in slots["intro"]:  # as the person placed them on Friends (2026-10-26): the hook on beat 2, again mid-intro, a line under the guitars
        if z - a >= 8:
            if a + 0.25 + bars_of(hook) <= a + (z - a) // 2 - 2:
                e.append([a, 4, hook, 80, 60])
            run(a + (z - a) // 2 - 2, z - 2, (hook,), 80, False)
            if z - a >= 16 and (not e or e[-1][0] + bars_of(e[-1][2]) <= z - 4 + 0.3):
                e.append([z - 4, 0, line, 88, 60])
    def answer(a: int, z: int) -> None:
        """The line answers into the drop and has finished as the drop comes in (the person moved it so on both songs, 2026-10-26)."""
        k = max(1, math.ceil(bars_of(line) - 0.15))
        if z - k < a:
            return
        mine = [r for r in e if a <= r[0] < z]
        if not mine or mine[-1][0] + mine[-1][1] / 16 + bars_of(mine[-1][2]) <= z - k + 0.3:
            e.append([z - k, 0, line, 100, 60])
    for a, z in slots["build"]:
        run(a, z - 1 + 0.25, (line, hook), 88, True)
        answer(a, z)
    for a, z in slots.get("answer", []):
        answer(a, z)
    for a, z in slots["tail"]:
        run(a, z, (hook, line), 104, False)
    for a, z in slots["outro"]:
        run(a + 2, min(z, a + 12), (line, hook), 82, False)
    return sorted(e)


def harmony_roots(x, rate: int, origin_s: float, bar_s: float, first_bar: int, n_bars: int, key_pc: int, mode: str = "major") -> list:
    """A root per bar (pitch-class names, None where the bar is quiet) from a harmony stem's chroma, for songs whose bass stem holds no bass
    ("Girls": a drum machine, a vibraphone riff and a sung bass voice). Each bar's pitch-class energy (80 Hz to 2 kHz) is matched against the
    key's own triads (I, ii, iii, IV, V, vi in major), root weighted most; bars count from first_bar as stem_notes.json's roots do."""
    import numpy as np

    from . import dsp
    m = dsp.mono(x) if getattr(x, "ndim", 1) > 1 else x
    hop, n_fft = 1024, 8192
    mag = dsp.stft_mag(m.astype(np.float64), n_fft=n_fft, hop=hop)  # (frames, bins)
    freqs = np.fft.rfftfreq(n_fft, 1.0 / rate)
    sel = (freqs >= 80) & (freqs <= 2000)
    pcs = (np.round(12 * np.log2(freqs[sel] / 440.0)).astype(int) + 9) % 12
    steps = MAJOR if mode != "minor" else MINOR
    triads = []
    for d, st in enumerate(steps):
        root = (key_pc + st) % 12
        third = (key_pc + steps[(d + 2) % 7]) % 12
        fifth = (key_pc + steps[(d + 4) % 7]) % 12
        if (fifth - root) % 12 == 7:  # leave out the diminished triad
            triads.append((root, third, fifth))
    frame_t = (np.arange(mag.shape[0]) * hop + n_fft / 2) / rate
    energy = []
    chroma = []
    for b in range(first_bar, first_bar + n_bars):
        t0, t1 = origin_s + b * bar_s, origin_s + (b + 1) * bar_s
        fr = mag[(frame_t >= t0) & (frame_t < t1)]
        c = np.zeros(12)
        if len(fr):
            np.add.at(c, pcs, (fr[:, sel] ** 2).sum(axis=0))
        chroma.append(c)
        energy.append(c.sum())
    loud = max(energy) if energy else 0.0
    names = "C C# D D# E F F# G G# A A# B".split()
    out = []
    for c, e in zip(chroma, energy):
        if loud <= 0 or e < loud * 1e-3:
            out.append(None)
            continue
        c = c / c.sum()
        best = max(triads, key=lambda t: c[t[0]] * 1.2 + c[t[1]] + c[t[2]] * 0.8)
        out.append(names[best[0]])
    return out


def bar_roots(src_bar: list, roots_per_bar: list, first_bar: int, key_pc: int, mode: str = "major") -> list:
    """The root each remix bar plays: the original's bass root on the source bar it carries (out-of-key passing notes replaced), where that bar
    had no bass the root eight or sixteen bars later (the progression repeats), else None (the plan's loop)."""
    roots = scale_roots(roots_per_bar, key_pc, mode)

    def at(b: int):
        i = b - first_bar
        return roots[i] if 0 <= i < len(roots) else None
    out = []
    for b in src_bar:
        r = None
        if b is not None:
            for k in (0, 8, 16, 24, -8):
                r = at(b + k)
                if r is not None:
                    break
        out.append(r)
    return out


def keys_notes(sections: list[dict], roots: list, qualities: dict, strum: str, key_pc: int, plays=("drop", "groove#2", "outro")) -> list[list]:
    """(beat, beats, key, velocity) rows for the song's chords on the chord synth: on every bar of the sections in `plays` (a kind, or kind#n
    for its n-th one) that carries a source root, the reference file's strum with that root's chord (midiref.voicing: a close triad or a
    bare fifth, at most three notes between A3 and A4). Without a quality from the file the key's own triad is used."""
    from . import midiref

    seen: dict = {}
    want = []
    for sec in sections:
        seen[sec["name"]] = seen.get(sec["name"], 0) + 1
        if sec["name"] in plays or "%s#%d" % (sec["name"], seen[sec["name"]]) in plays:
            want.append(sec)
    hits = [i for i, c in enumerate(strum) if c in "Xx"] or [0, 4, 8, 12]
    step = 4.0 / len(strum)
    out = []
    for sec in want:
        last = sec["end"] if sec["name"] != "outro" else min(sec["end"], sec["start"] + 8)
        for b in range(sec["start"], last):
            r = roots[b] if b < len(roots) else None
            if r is None:
                continue
            q = qualities.get(r) or ("min" if (r - key_pc) % 12 in (2, 4, 9) else "maj")
            for n, i in enumerate(hits):
                nxt = hits[n + 1] if n + 1 < len(hits) else len(strum)
                dur = min(1.0, (nxt - i) * step * 0.9)
                vel = 100 if strum[i] == "X" else 82
                out += [[round(b * 4 + i * step, 4), round(dur, 4), k, vel] for k in midiref.voicing(r, q)]
    return out
