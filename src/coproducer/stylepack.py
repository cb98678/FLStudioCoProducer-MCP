"""Style packs: a genre as data (styles/<name>.json), and the grammar engine that turns one into drum, bass and chord parts for a song plan.

A pack holds the tempo strategy, the section template, step patterns per section kind for every drum voice, bass and sub, chord hits, the drum kit
and bass sample to synthesize, the production recipe, the targets file and the sources the numbers came from. "tech_house" keeps the hand-written
engine in remixplan (the first song's regression build); every other pack runs through the grammar here, so a new genre is a new JSON file.

Patterns are strings, one character per step: 16 characters is a bar of 16ths, 32 a bar of 32nds, 8 a bar of 8ths, 12 and 24 triplet 8ths and
16ths. Drums: X accent, x normal, o soft, anything else is a rest. Bass and chords: x root, X accented root, o root an octave up, 5 the fifth,
v the fifth below, 4 the fourth, 7 the minor seventh, 3 the chord's third, b the flat second, d an octave down, - holds the previous note,
. rests (the demo study's lines need them: a trance roll's seventh, a pop bass's low fifth, a trap 808's Phrygian step, 2026-10-28).
A pattern may also be a list, played one bar after another. Bars count from 0 in a section; "last" replaces voices on its last bar (a pre-drop
mute), "fill_every" puts a drumplan fill on every n-th bar, "roll" makes a build's snare speed up from quarters to 32nds. drums.swing (0.5 to 0.75,
MPC-style) delays every off 16th; tempo.follow (default true) lets pick_tempo keep the source's own tempo when it is in range.
"""
from __future__ import annotations

import math

import json
from pathlib import Path

from . import drumplan, tension

STYLES = Path(__file__).resolve().parents[2] / "styles"
DRUM_VEL = {"X": 1.0, "x": 0.8, "o": 0.5}
VOICES = ("kick", "snare", "clap", "hat", "ohat", "shaker", "rim", "tom", "crash", "perc", "ride")
STEPS = (8, 12, 16, 24, 32)  # pattern lengths: 8ths, triplet 8ths, 16ths, triplet 16ths, 32nds
OFFSETS = {"v": -5, "4": 5, "7": 10, "b": 1, "d": -12}  # semitones from the bar's root for the bass characters beyond x, o and 5
REQUIRED = ("name", "label", "engine", "tempo", "sections", "sources", "production_recipe", "targets")


class StyleError(ValueError):
    """A pack that cannot drive a build; the message says which field."""


def names() -> list[str]:
    return sorted(p.stem for p in STYLES.glob("*.json"))


def for_mood(feel: list[str]) -> list[dict]:
    """Packs whose "moods" share a word with the song's mood (the creative brief), best first: [{style, matched}]. A starting map to argue
    with per song (skill genre-styles, step 0); an empty list means no pack fits yet, a reason to add one rather than force the nearest."""
    want = {w.strip().lower() for w in feel or [] if w and w.strip()}
    rows = []
    for n in names():
        got = [m for m in json.loads((STYLES / ("%s.json" % n)).read_text(encoding="utf-8")).get("moods", []) if m in want]
        if got:
            rows.append({"style": n, "matched": got})
    return sorted(rows, key=lambda r: (-len(r["matched"]), r["style"]))


def load(name: str) -> dict:
    p = STYLES / ("%s.json" % name)
    if not p.is_file():
        raise StyleError("no style %r (known: %s)" % (name, ", ".join(names())))
    pack = json.loads(p.read_text(encoding="utf-8"))
    bad = validate(pack)
    if bad:
        raise StyleError("style %s: %s" % (name, "; ".join(bad)))
    return pack


def validate(pack: dict) -> list[str]:
    out = ["missing field: " + k for k in REQUIRED if k not in pack]
    if out:
        return out
    if pack["engine"] not in ("techhouse", "grammar"):
        out.append("engine must be techhouse or grammar")
    lo, hi = pack["tempo"].get("range", [pack["tempo"]["bpm"]] * 2)
    if not lo <= pack["tempo"]["bpm"] <= hi:
        out.append("tempo bpm outside its range")
    for kind, bars in pack["sections"]:
        if kind not in ("intro", "groove", "break", "build", "drop", "outro") or int(bars) < 1:
            out.append("bad section %r" % kind)
    if pack["engine"] == "grammar":
        sw = pack.get("drums", {}).get("swing", 0.5)
        if not isinstance(sw, (int, float)) or not 0.5 <= sw <= 0.75:
            out.append("drums.swing must be a number from 0.5 (straight) to 0.75")
        for kind, spec in pack.get("drums", {}).items():
            if kind == "swing":
                continue
            if not isinstance(spec, dict):
                out.append("drums.%s must be an object" % kind)
                continue
            for inst in list(spec.get("bars", {})) + list(spec.get("last", {})):
                if inst not in VOICES:
                    out.append("drums.%s: unknown voice %s" % (kind, inst))
            for pats in list(spec.get("bars", {}).values()) + list(spec.get("last", {}).values()):
                for pat in pats if isinstance(pats, list) else [pats]:
                    if len(pat) not in STEPS:
                        out.append("drums.%s: pattern %r is not 8, 12, 16, 24 or 32 steps" % (kind, pat))
        for role in ("bass", "sub", "chords"):
            for kind, pats in pack.get(role, {}).items():
                if kind in LINE_KEYS:
                    continue
                for pat in pats if isinstance(pats, list) else [pats]:
                    if len(pat) not in STEPS:
                        out.append("%s.%s: pattern %r is not 8, 12, 16, 24 or 32 steps" % (role, kind, pat))
        v = pack.get("chords", {}).get("voicing", "triad")
        if v not in VOICINGS:
            out.append("chords.voicing must be one of %s" % ", ".join(VOICINGS))
        pad = pack.get("pad") or {}
        for kind, how in pad.items():
            if kind in ("voicing", "base", "max_bars", "velocity", "sound", "lead"):
                continue
            if kind not in ("intro", "groove", "break", "build", "drop", "outro") or how not in PAD_MODES:
                out.append("pad.%s must be one of %s" % (kind, ", ".join(PAD_MODES)))
        if pad and pad.get("voicing", "add9") not in VOICINGS:
            out.append("pad.voicing must be one of %s" % ", ".join(VOICINGS))
        arp = pack.get("arp", [])
        if isinstance(arp, dict):
            if arp.get("shape", "rise") not in ARP_SHAPES:
                out.append("arp.shape must be one of %s" % ", ".join(ARP_SHAPES))
            if int(arp.get("rate", 16)) not in STEPS:
                out.append("arp.rate must be 8, 12, 16, 24 or 32")
    if not pack["sources"]:
        out.append("sources must cite where the numbers come from")
    return out


MULTIPLES = (0.5, 1.0, 2.0)


MAX_SPEEDUP = 1.35  # past this the voice sounds rushed; a style that cannot stay under it says so in the plan notes
MAX_SLOWDOWN = 0.94  # the person (2026-10-28): a vocal may run a little slower, "but not too slow and preserve pitch": at most 6 % slower
SLOW_COST = 1.5      # a slowdown counts this much more than a speed-up of the same size (a slowed voice drags sooner than a faster one rushes)


def stretch_of(bpm: float, multiple: float, source_bpm: float) -> float:
    """How fast the vocal runs against how it was sung: 1.0 is its own tempo, above 1 faster, below 1 slower (never below MAX_SLOWDOWN).
    The pitch and formants stay where they were (remixaudio stretches with rubberband, formant preserved)."""
    return bpm * multiple / source_bpm


def stretch_cost(st: float) -> float:
    """How far a stretch moves the voice: the size of the change, a slowdown weighted by SLOW_COST; outside MAX_SLOWDOWN to MAX_SPEEDUP it
    is not allowed (infinite)."""
    if not MAX_SLOWDOWN - 1e-9 <= st <= MAX_SPEEDUP + 1e-9:
        return math.inf
    d = abs(math.log(st))
    return d * SLOW_COST if st < 1 else d


def vocal_multiple(bpm: float, source_bpm: float) -> float:
    """The tempo the original vocal runs at, as a multiple of the remix tempo: 1 (same tempo), 0.5 (one vocal bar over two remix bars) or 2,
    whichever changes the voice least within the allowed stretch (at most 6 % slower, at most 35 % faster). Dubstep at 140 over 108.5 keeps
    1 (x1.29); drum and bass at 174 keeps 1 (x1.60) where half time would be x0.80, far too slow. When nothing is allowed, the least
    speed-up that does not slow the voice, as before."""
    ok = [m for m in MULTIPLES if stretch_cost(stretch_of(bpm, m, source_bpm)) < math.inf]
    if ok:
        return min(ok, key=lambda m: stretch_cost(stretch_of(bpm, m, source_bpm)))
    faster = [m for m in MULTIPLES if stretch_of(bpm, m, source_bpm) >= 0.999]
    return min(faster, key=lambda m: stretch_of(bpm, m, source_bpm)) if faster else max(MULTIPLES)


def pick_tempo(pack: dict, source_bpm: float) -> float:
    """The remix tempo under the person's rules: the vocal at its own tempo, faster, or a little slower (at most 6 %, pitch kept; 2026-10-28;
    before that never slower, after hip-hop at 0.83x and drum and bass at 0.80x sounded long and drawn out on 2026-10-25). In order: the
    source's own tempo (or its half or double) when it lies in the pack's range, nearest the pack's bpm (no stretch at all); else the tempo in
    range that changes the voice least (stretch_cost); else, when nothing in range is allowed and tempo.follow is not false, the source's own
    tempo outside the range (a rap beat at the song's tempo beats a rushed voice). A pack with follow false (a genre DJs play at one tempo,
    drum and bass) keeps its range and the plan notes the speed-up."""
    t = pack["tempo"]
    lo, hi = t.get("range", [t["bpm"]] * 2)
    exact = [source_bpm / m for m in MULTIPLES if lo <= source_bpm / m <= hi]
    if exact and t.get("follow", True) is not False:
        return round(min(exact, key=lambda b: abs(b - t["bpm"])), 3)
    best = None
    for m in MULTIPLES:
        bpm = min(hi, max(lo, source_bpm / m))          # the tempo in range nearest the vocal's own
        c = stretch_cost(stretch_of(bpm, m, source_bpm))
        if best is None or c < best[0]:
            best = (c, round(bpm, 3), m)
    if best[0] == math.inf:
        if t.get("follow", True) is not False:
            return round(source_bpm, 3)
        faster = [(stretch_of(max(lo, source_bpm / m), m, source_bpm), round(max(lo, source_bpm / m), 3)) for m in MULTIPLES
                  if max(lo, source_bpm / m) <= hi]
        return min(faster)[1] if faster else float(t["bpm"])
    return best[1]


def standard_tempo(pack: dict, source_bpm: float) -> float | None:
    """The style's own tempo when the vocal can run there (within MAX_SLOWDOWN to MAX_SPEEDUP, a form option's tempo "standard": Freejak took
    Sorry from 100 to house's 128, x1.28, where pick_tempo takes the least change). None when it cannot."""
    bpm = float(pack["tempo"]["bpm"])
    st = stretch_of(bpm, vocal_multiple(bpm, source_bpm), source_bpm)
    return bpm if stretch_cost(st) < math.inf else None


def sections_for(pack: dict) -> tuple:
    return tuple((k, int(n)) for k, n in pack["sections"])


def _steps(pat: str) -> list[tuple[float, str]]:
    scale = 16 / len(pat)
    return [(i * scale, c) for i, c in enumerate(pat)]


def _pick(pats, k: int) -> str:
    return pats[k % len(pats)] if isinstance(pats, list) else pats


def drums(pack: dict, sections: list[dict]) -> drumplan.Plan:
    """The drum plan of a song: for each section, its kind's patterns bar by bar, the last-bar overrides, fills and the accelerating roll.
    A form (pack["form"]) can drop the drums out of every n-th groove or drop (drum_dropout_every) and empty the last beat or bar before
    each drop (gap_before_drop)."""
    plan = drumplan.Plan()
    spec_all = pack.get("drums", {})
    late = (float(spec_all.get("swing", 0.5)) - 0.5) * 2  # MPC-style swing: 0.5 straight, 0.58 puts each off 16th at 58 % of its 8th
    form = pack.get("form") or {}
    dropout = int(form.get("drum_dropout_every") or 0)
    count = 0
    for s in sections:
        spec = spec_all.get(s["name"]) or spec_all.get("default", {})
        if dropout and s["name"] in ("groove", "drop"):
            count += 1
            if count % dropout == 0:
                spec = spec_all.get("break", {})   # loop-block songs: every n-th block without kick and snare
        n = s["end"] - s["start"]
        v0, v1 = spec.get("ramp", [1.0, 1.0])
        for b in range(s["start"], s["end"]):
            plan.labels[b] = s["name"]
            k = b - s["start"]
            g = v0 + (v1 - v0) * (k / max(n - 1, 1))
            voices = dict(spec.get("bars", {}))
            if k == n - 1:
                voices.update(spec.get("last", {}))
            for inst, pats in voices.items():
                for step, c in _steps(_pick(pats, k)):
                    if c in DRUM_VEL:
                        pan = 0.14 * (1 if int(step) % 4 >= 2 else -1) if inst in ("hat", "ohat", "shaker") else 0.0
                        sw = late if late and float(step).is_integer() and int(step) % 2 == 1 else 0.0
                        plan.ev(b, step + sw, inst, DRUM_VEL[c] * g, pan)
            every = int(spec.get("fill_every", 0))
            if every and k % every == every - 1 and k != n - 1:
                plan.fill(b, spec.get("fill", "A"))
            if spec.get("roll") == "accelerate":
                p = k / n
                div = drumplan.ROLL_DIVISIONS[min(3, int(p * 4))]
                last = k == n - 1
                plan.roll(b, 0, 14 if last else 16, div, 0.35 + 0.35 * p if not last else 0.7, 0.55 + 0.35 * p if not last else 1.0)
    for b, g in drumplan.default_crashes(sections).items():
        plan.ev(b, 0, "crash", g, 0.15 if b % 8 else -0.15)
    gap = form.get("gap_before_drop")
    if gap in ("beat", "bar"):
        for a, z in zip(sections, sections[1:]):
            if z["name"] == "drop" and a["name"] != "drop":
                last = a["end"] - 1
                plan.events = [e for e in plan.events if not (e[0] == last and (gap == "bar" or e[1] >= 12))]
    return plan


LINE_KEYS = ("pedal", "voicing", "top_only", "bass_between")  # settings kept in a role's object beside its patterns


def _key_for(c: str, pc: int, key_of, third: int = 4) -> int | None:
    if c in "xX":
        return key_of(pc, 0)
    if c == "o":
        return key_of(pc, 1)
    if c == "5":
        return key_of((pc + 7) % 12, 0)
    if c == "3":
        return key_of(pc, 0) + third
    if c in OFFSETS:
        return key_of(pc, 0) + OFFSETS[c]
    return None


def _root(root_at, bar: int, step: float = 0.0) -> int:
    """The chord root at a step of a bar: root_at(bar, step) when it takes a step (a loop that changes chord inside a bar), else
    root_at(bar)."""
    try:
        return root_at(bar, step)
    except TypeError:
        return root_at(bar)


def _change_in(root_at, bar: int, a: float, z: float) -> float | None:
    """The first 16th step after a and before z where the bar's chord root changes, or None."""
    first = _root(root_at, bar, a)
    s = int(math.floor(a)) + 1
    while s < z:
        if _root(root_at, bar, s) != first:
            return float(s)
        s += 1
    return None


def line_notes(pack: dict, role: str, sections: list[dict], root_at, key_of, third_of=None, tonic: int | None = None) -> list[tuple]:
    """(start_beat, dur_beats, key, velocity) for a bass or sub line: the role's pattern per section kind, notes held through '-' steps.
    third_of(pc) gives the chord's third in semitones for '3' (default a major third); a role's "pedal" list names section kinds that hold
    the tonic instead of following the chords (an intro drone)."""
    out: list[tuple] = []
    pats_all = pack.get(role, {})
    pedal = set(pats_all.get("pedal", [])) if isinstance(pats_all.get("pedal"), list) else set()
    for s in sections:
        pats = pats_all.get(s["name"])
        if not pats or s["name"] in LINE_KEYS:
            continue
        for b in range(s["start"], s["end"]):
            pat = _pick(pats, b - s["start"])
            steps = _steps(pat)
            unit = 16 / len(pat)
            pedal_here = s["name"] in pedal and tonic is not None
            for i, (step, c) in enumerate(steps):
                pc = tonic if pedal_here else _root(root_at, b, step)
                key = _key_for(c, pc, key_of, third_of(pc) if third_of else 4)
                if key is None:
                    continue
                j = i + 1
                while j < len(steps) and steps[j][1] == "-":
                    j += 1
                vel = 120 if c == "X" else 104
                end = step + (j - i) * unit
                cut = None if pedal_here else _change_in(root_at, b, step, end)
                if cut is None:
                    out.append(((b * 16 + step) / 4, (j - i) * unit / 4 * 0.95, key, vel))
                    continue
                # a held note across a chord change: the note to the change, then the new root (re-struck) to the note's end
                out.append(((b * 16 + step) / 4, (cut - step) / 4 * 0.95, key, vel))
                pc2 = _root(root_at, b, cut)
                key2 = _key_for(c, pc2, key_of, third_of(pc2) if third_of else 4)
                if key2 is not None:
                    out.append(((b * 16 + cut) / 4, (end - cut) / 4 * 0.95, key2, vel))
    return out


VOICINGS = ("triad", "seventh", "add9", "sus2", "sus4", "open", "octaves", "minmaj", "scale_run")
ARP_SHAPES = ("rise", "fall", "updown", "pedal", "octave", "broken", "tresillo", "chromatic", "sequence")
SCALES = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10)}


def voice(keys: list[int], voicing: str = "triad", dominant: bool = False) -> list[int]:
    """A triad's keys (root, third, fifth, ascending) in a voicing: seventh (minor seventh on a minor triad, major seventh on a major one,
    minor seventh when dominant), add9, sus2, sus4, open (root, fifth, tenth), octaves (the root again an octave up), minmaj (minor with a
    major seventh). Any other voicing is the triad."""
    r, t, f = keys[0], keys[1], keys[2]
    minor = t - r == 3
    if voicing == "seventh":
        return [r, t, f, r + (10 if minor or dominant else 11)]
    if voicing == "add9":
        return [r, t, f, r + 14]
    if voicing == "sus2":
        return [r, r + 2, f]
    if voicing == "sus4":
        return [r, r + 5, f]
    if voicing == "open":
        return [r, f, t + 12]
    if voicing == "octaves":
        return [r, t, f, r + 12]
    if voicing == "minmaj":
        return [r, r + 3, f, r + 11]
    return [r, t, f]


def scale_keys(key_pc: int, mode: str, lo: int, hi: int) -> list[int]:
    """Every key of the scale from lo to hi inclusive."""
    pcs = {(key_pc + st) % 12 for st in SCALES.get(mode, SCALES["major"])}
    return [k for k in range(lo, hi + 1) if k % 12 in pcs]


def snap(key: int, key_pc: int, mode: str) -> int:
    """The nearest key of the scale (down first on a tie)."""
    for d in (0, -1, 1, -2, 2):
        if (key + d - key_pc) % 12 in SCALES.get(mode, SCALES["major"]):
            return key + d
    return key


def chord_notes(pack: dict, sections: list[dict], root_at, chord_keys, key_pc: int | None = None, mode: str = "major") -> list[tuple]:
    """Chord hits or pads: the bar's chord, in the pack's voicing (chords.voicing), at each x, X or o of the section kind's pattern (o an
    octave up), held through '-'. chords.top_only plays only the voicing's top note (a bell ostinato); voicing scale_run plays two notes of
    the key's scale per hit, climbing from the root (a harp glissando)."""
    out: list[tuple] = []
    spec = pack.get("chords", {})
    voicing, top_only = spec.get("voicing", "triad"), bool(spec.get("top_only"))
    for s in sections:
        pats = spec.get(s["name"])
        if not pats or s["name"] in LINE_KEYS:
            continue
        for b in range(s["start"], s["end"]):
            pat = _pick(pats, b - s["start"])
            steps, unit = _steps(pat), 16 / len(pat)
            hits = [i for i, (_st, c) in enumerate(steps) if c in "xXo"]
            for n, i in enumerate(hits):
                step, c = steps[i]
                j = i + 1
                while j < len(steps) and steps[j][1] == "-":
                    j += 1
                end = step + (j - i) * unit
                cut = _change_in(root_at, b, step, end)
                for a0, a1 in ((step, end),) if cut is None else ((step, cut), (cut, end)):   # a held chord re-voiced at a chord change
                    pc = _root(root_at, b, a0)
                    base = chord_keys(pc, 72 if c == "o" else 60)
                    if voicing == "scale_run" and key_pc is not None:
                        run = scale_keys(key_pc, mode, base[0], base[0] + 30)
                        keys = run[2 * n:2 * n + 2] or [base[0]]
                    else:
                        dom = key_pc is not None and (pc - key_pc) % 12 == (7 if mode == "major" else 10)
                        keys = voice(base, voicing, dominant=dom)
                    if top_only:
                        keys = [max(keys)]
                    for k in keys:
                        out.append(((b * 16 + a0) / 4, (a1 - a0) / 4 * 0.95, k, 122 if c == "X" else 108))
    return out


PAD_MODES = ("chord", "bar", "half")   # held to the next chord change, re-struck every bar, or every half bar


def _pad_starts(root_at, s: dict, how: str, max_bars: int) -> list[int]:
    """16th steps (song time) where a pad chord starts in a section: its start, every chord change, every bar or half bar for those modes,
    and a re-strike after max_bars of one held chord."""
    a, z = s["start"] * 16, s["end"] * 16
    marks, cur = {a}, _root(root_at, s["start"], 0.0)
    for q in range(a + 1, z):
        r = _root(root_at, q // 16, float(q % 16))
        if r != cur:
            marks.add(q)
            cur = r
    if how in ("bar", "half"):
        marks |= set(range(a, z, 16 if how == "bar" else 8))
    out = []
    for q in sorted(marks):
        while out and q - out[-1] > max_bars * 16:
            out.append(out[-1] + max_bars * 16)
        out.append(q)
    while out and z - out[-1] > max_bars * 16:
        out.append(out[-1] + max_bars * 16)
    return out


def lead_voices(prev: list[int] | None, keys: list[int], lo: int, hi: int) -> list[int]:
    """The chord's tones in the inversion and octave nearest the previous chord, inside lo..hi: common tones held, the rest moving by
    the smallest steps (voice leading; Red Lights' pad moves its upper voices four semitones in four bars while the bass leaps)."""
    if not prev:
        return keys
    pcs, best = [k % 12 for k in keys], None
    for rot in range(len(pcs)):
        order = pcs[rot:] + pcs[:rot]
        for octave in range(lo // 12 - 1, hi // 12 + 1):
            v = [12 * octave + order[0]]
            for pc in order[1:]:
                v.append(v[-1] + ((pc - v[-1]) % 12 or 12))
            if v[0] < lo or v[-1] > hi:
                continue
            a, b = sorted(prev), v
            cost = sum(abs(x - y) for x, y in zip(a, b)) + 12 * abs(len(a) - len(b))
            if best is None or cost < best[0]:
                best = (cost, v)
    return best[1] if best else keys


def pad_notes(pack: dict, sections: list[dict], root_at, chord_keys, key_pc: int | None = None, mode: str = "major") -> list[tuple]:
    """A held pad under the stabs (pack "pad": a mode per section kind from PAD_MODES, voicing default add9, base default 48, an octave
    under the stabs, max_bars default 4, velocity per kind default 92; "sound" names the sound option whose envelope a generated pad
    takes). Each chord rings to the next start, never past its section."""
    spec = pack.get("pad") or {}
    voicing, base, max_bars = spec.get("voicing", "add9"), int(spec.get("base", 48)), int(spec.get("max_bars", 4))
    vel, prev = spec.get("velocity", {}), None
    out: list[tuple] = []
    for s in sections:
        how = spec.get(s["name"])
        if how not in PAD_MODES:
            continue
        starts = _pad_starts(root_at, s, how, max_bars)
        for i, q in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else s["end"] * 16
            pc = _root(root_at, q // 16, float(q % 16))
            dom = key_pc is not None and (pc - key_pc) % 12 == (7 if mode == "major" else 10)
            keys = voice(chord_keys(pc, base), voicing, dominant=dom)
            if spec.get("lead"):   # voice-led: each chord in the inversion nearest the last, within about an octave and a half
                keys = prev = lead_voices(prev, keys, base - 5, base + 19)
            for k in keys:
                out.append((q / 4, (end - q) / 4 * 0.97, k, int(vel.get(s["name"], 92))))
    return out


def _arp_keys(shape: str, tones: list[int], n: int, rhythm: str | None, cell: list[int] | None, root: int, key_pc: int | None, mode: str) -> list[int | None]:
    """The key for each of n steps of one bar (None: a rest)."""
    if shape == "sequence" and cell:
        ks = [root + c for c in cell]
        if key_pc is not None:
            ks = [snap(k, key_pc, mode) for k in ks]
        return [ks[i % len(ks)] for i in range(n)]
    if shape == "octave":
        pat = rhythm or "x.x.o.x.x.o.x.o."
        return [root if c in "xX" else root + 12 if c == "o" else None for c in (pat * (n // len(pat) + 1))[:n]]
    if shape == "chromatic":
        pat = rhythm or "x.xx.xx.xx.xx..."
        top, out, k = max(tones), [], 0
        for c in (pat * (n // len(pat) + 1))[:n]:
            out.append(top - k if c in "xX" else None)
            k += 1 if c in "xX" else 0
        return out
    if shape == "fall":
        seq = sorted(tones, reverse=True)
    elif shape == "updown":
        up = sorted(tones)
        seq = up + up[-2:0:-1]
    elif shape == "pedal":
        lo, ups = min(tones), sorted(tones)[1:] or [min(tones) + 12]
        seq = [x for u in ups for x in (lo, u)]
    elif shape == "broken":
        up = sorted(tones)
        idx = [0, 2, 4, 5, 4, 2] if len(up) >= 6 else [0, min(2, len(up) - 1), len(up) - 1, min(2, len(up) - 1)]
        seq = [up[min(i, len(up) - 1)] for i in idx]
    elif shape == "tresillo":
        up = sorted(tones)
        pat = rhythm or "xx.xxx.xxx.xxx.x"
        out, k = [], 0
        for i, c in enumerate((pat * (n // len(pat) + 1))[:n]):
            if c in "xX":
                key = [up[0], up[min(2, len(up) - 1)], up[min(1, len(up) - 1)]][k % 3]
                out.append(key + (12 if i % 4 == 0 and k % 3 == 0 else 0))
                k += 1
            else:
                out.append(None)
        return out
    else:
        seq = sorted(tones)
    if rhythm:
        pat, out, k = (rhythm * (n // len(rhythm) + 1))[:n], [], 0
        for c in pat:
            out.append(seq[k % len(seq)] if c in "xX" else None)
            k += 1 if c in "xX" else 0
        return out
    return [seq[i % len(seq)] for i in range(n)]


def arp_notes(pack: dict, sections: list[dict], root_at, chord_keys, key_pc: int | None = None, mode: str = "major") -> list[tuple]:
    """The arp part. A list (the older packs) is the rising 16th arpeggio (tension.rising_arp) in those section kinds, from the middle of a
    break. An object is a shape from the demo study: {"shape", "rate" (steps a bar: 8, 12 triplet 8ths, 16, 24), "sections", "octaves",
    "double" (semitones to add above each note, [12, 24] for an octave-doubled bell), "rhythm" (x a note, . a rest, o the octave for
    shape octave; a list is one rhythm a bar in turn), "cell" (semitones over the root for shape sequence, snapped to the key's scale), "gate" (note length as a share of a
    step), "voicing"}. Builds ramp the velocity up; other sections accent the beats."""
    spec = pack.get("arp", [])
    out: list[tuple] = []
    if not isinstance(spec, dict):
        for s in sections:
            if s["name"] not in spec:
                continue
            n = s["end"] - s["start"]
            start = s["start"] + (n // 2 if s["name"] == "break" else 0)
            chords = [chord_keys(root_at(b), 72) + [chord_keys(root_at(b), 84)[0]] for b in range(start, s["end"])]
            if chords:
                out += tension.rising_arp(start, chords, v0=64, bar_ramp=int(60 / len(chords)))
        return out
    shape, rate = spec.get("shape", "rise"), int(spec.get("rate", 16))
    octaves, gate = int(spec.get("octaves", 1)), float(spec.get("gate", 0.8))
    double = [int(d) for d in spec.get("double", [])]
    step_beats = 4.0 / rate
    for s in sections:
        if s["name"] not in spec.get("sections", ["break", "build"]):
            continue
        n_bars = s["end"] - s["start"]
        for b in range(s["start"], s["end"]):
            rhythm = _pick(spec["rhythm"], b - s["start"]) if spec.get("rhythm") else None   # a list: one rhythm a bar, in turn
            cut = _change_in(root_at, b, 0.0, 16.0)
            halves = {}
            for a0 in (0.0,) if cut is None else (0.0, cut):     # the arp's notes follow the chord change inside the bar
                base = chord_keys(_root(root_at, b, a0), 72)
                tones = voice(base, spec.get("voicing", "triad"))
                if octaves > 1:
                    tones = tones + [t + 12 for t in tones]
                halves[a0] = _arp_keys(shape, tones, rate, rhythm, spec.get("cell"), base[0], key_pc, mode)
            k_bar = b - s["start"]
            for i in range(rate):
                at = i * 16.0 / rate
                key = halves[cut if cut is not None and at >= cut else 0.0][i]
                if key is None:
                    continue
                if s["name"] == "build":
                    vel = 64 + int(56 * (k_bar * rate + i) / max(1, n_bars * rate - 1))
                else:
                    vel = 104 if (i * step_beats) % 1.0 < 1e-6 else 88
                for d in [0] + double:
                    out.append(((b * 4) + i * step_beats, step_beats * gate, key + d, vel - (10 if d else 0)))
    return out
