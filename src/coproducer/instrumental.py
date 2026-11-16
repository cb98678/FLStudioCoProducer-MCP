"""An original track with no source song (the person, 2026-11-07: "make me an awesome dubstep song, original").

The remix pipeline reads everything about a song from its plan, so an original needs only a plan with no vocal in it: no chops, no clips,
no words; the style pack's drums, bass, sub, chords and arp as usual, and the parts the person or the agent wrote (a bass line, a sub, keys,
a pad, a lead) as note lists in true MIDI on the plan's "part_notes". A part named in "omit_parts" gets no channel. prepare_remix_audio
then writes the kit, the bass sample and the FX bed without a vocal stem, and build_remix_project writes no vocal channel.

Part note lists are [[start beat, length beats, MIDI note, velocity], ...] with beat 0 the first bar of the arrangement; a MIDI file's
notes are read the same way, every track merged, beats as the file wrote them (the file's tempo is not used: a part written at the plan's
tempo lands on its grid).
"""
from __future__ import annotations

from pathlib import Path

from . import arrange, midiref, stylepack

PART_ROLES = ("bass", "sub", "keys", "pad", "lead")   # part_notes keys: the build's reese, sub, stab, pad and arp channels
PART_CHANNEL = {"bass": "reese", "sub": "sub", "keys": "stab", "pad": "pad", "lead": "arp"}
OMITTABLE = ("bass", "sub", "keys", "pad", "lead", "arp", "stab", "reese")   # omit_parts accepts the part's name or its channel's


def notes_from_midi(path: str | Path, bar: int = 0) -> list[list]:
    """A MIDI file's notes as plan rows [start beat, length beats, MIDI note, velocity], every track merged and sorted, placed from `bar`
    (0-based) of the arrangement: a part written for one section starts at its section's first bar."""
    m = midiref.read(str(path))
    off = 4.0 * int(bar)
    out = [[round(b0 + off, 4), round(max(b1 - b0, 0.0625), 4), int(p), int(v)] for t in m["tracks"] for b0, b1, p, v in t["notes"]]
    return sorted(out)


def part_files_notes(spec) -> list[list]:
    """The rows of one role's files: a path, "path@BAR" (placed from that 0-based bar), or a list of those, merged in time order."""
    rows: list[list] = []
    for item in ([spec] if isinstance(spec, str) else list(spec)):
        path, bar = (item.rsplit("@", 1) if "@" in str(item) and str(item).rsplit("@", 1)[1].isdigit() else (item, 0))
        rows += notes_from_midi(path, int(bar))
    return sorted(rows)


def check_notes(rows: list, bars: int) -> list[str]:
    """Problems with one part's rows: shape, pitch, velocity, and notes past the arrangement's end."""
    out = []
    for n in rows:
        if len(n) != 4 or float(n[1]) <= 0 or not 0 <= int(n[2]) <= 127 or not 1 <= int(n[3]) <= 127 or float(n[0]) < 0:
            out.append("note %r is not [start beat >= 0, length > 0, MIDI 0..127, velocity 1..127]" % (n,))
            break
    late = [n for n in rows if len(n) == 4 and float(n[0]) >= bars * 4]
    if late:
        out.append("%d notes start after the last bar (%d)" % (len(late), bars))
    return out


_PC = {n: i for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())} | {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}


def harmony(chords: list[str]) -> tuple[list[int], dict]:
    """An 8-bar loop from chord names ("Fm", "Db", "Ab", "Eb": four names hold two bars each, eight hold one): (roots8, root_quality with
    "min" for a minor chord, so the pack's stabs play the chord the name says)."""
    if len(chords) not in (4, 8):
        raise ValueError("give four chord names (two bars each) or eight (one bar each), got %d" % len(chords))
    roots, qual = [], {}
    for c in chords:
        name = c.strip()
        minor = name.endswith("m") and not name.endswith("maj")
        root = name[:-1] if minor else name
        if root not in _PC:
            raise ValueError("unknown chord name %r (use C, C#, Db ... with m for minor)" % c)
        roots += [_PC[root]] * (2 if len(chords) == 4 else 1)
        if minor:
            qual[str(_PC[root])] = "min"
    return roots, qual


def draft_plan(name: str, *, style: str, key_pc: int, mode: str = "minor", bpm: float | None = None, sections: list | None = None,
               roots8: list | None = None, chords: list | None = None, part_files: dict | None = None, part_notes: dict | None = None,
               omit: list | None = None, labels: dict | None = None, title: str = "", variety: dict | bool | None = False,
               notes: list | None = None) -> dict:
    """A plan for an original track: the style pack's sections (or the given [[kind, bars], ...]) and tempo, the key, a harmony loop (chords
    as names, or roots8 as pitch classes; the tonic alone when neither is given), the parts as note lists (part_notes by role, or
    part_files: role -> MIDI path), the parts to leave out, and the usual FX cues and 16-bar piano rolls. variety is off unless asked (the
    person's arrangement is the form); with a dict it chooses groove, kit and sounds the way a remix's draft does, and its form option may
    change the sections. Validate with songplan.validate before use."""
    from . import songanalysis
    qual: dict = {}
    if chords:
        roots8, qual = harmony(list(chords))
    pack = stylepack.load(style)
    bpm = float(bpm if bpm is not None else pack["tempo"]["bpm"])
    picked = songanalysis._variety(name, pack, variety, None, bpm, None) if variety else None
    if picked:
        pack = picked["pack"]
    secs, bars = [], 0
    for label, n in (sections or stylepack.sections_for(pack)):
        secs.append({"name": str(label), "start": bars, "end": bars + int(n)})
        bars += int(n)
    parts = {k: [list(map(float, n[:2])) + [int(n[2]), int(n[3])] for n in v] for k, v in (part_notes or {}).items()}
    for role, spec in (part_files or {}).items():
        parts[role] = part_files_notes(spec)
    bad = [r for r in parts if r not in PART_ROLES] + [r for r in (omit or []) if r not in OMITTABLE] + [r for r in (labels or {}) if r not in OMITTABLE]
    if bad:
        raise ValueError("unknown part or omit name(s): %s (parts: %s)" % (", ".join(bad), ", ".join(PART_ROLES)))
    problems = [r + ": " + p for r, v in parts.items() for p in check_notes(v, bars)]
    if problems:
        raise ValueError("; ".join(problems))
    plan = {"name": name, "title": title, "bpm": bpm, "source_bpm": bpm, "key_pc": int(key_pc) % 12, "origin_s": 0.0, "mode": mode,
            "roots8": [int(p) % 12 for p in roots8] if roots8 else [int(key_pc) % 12] * 8, "sections": secs, "chops": {}, "echoed": [],
            "vocal_clips": [], "clip_words": [], "chop_events": [], "fx_cues": arrange.generate_fx_cues(secs), "pattern_bars": 16,
            "instrumental": True, "support": {"mode": "off"}, "style": pack["name"], "vocal_multiple": 1.0,
            "part_notes": {k: v for k, v in parts.items() if v}, "omit_parts": sorted(set(omit or [])), **({"root_quality": qual} if qual else {}),
            **({"part_labels": {k: str(v) for k, v in labels.items()}} if labels else {}),
            "notes": ["original track, no source song: no vocal, no chops", "style %s at %g bpm, %d bars" % (pack["name"], bpm, bars),
                      "parts written for it: %s" % (", ".join(sorted(k for k, v in parts.items() if v)) or "none (the pack's own)"),
                      *(["left out: " + ", ".join(sorted(set(omit)))] if omit else []), *(notes or [])]}
    if len(plan["roots8"]) != 8:
        raise ValueError("roots8 needs eight pitch classes, one per bar of the loop")
    songanalysis._with_variety(plan, picked, int(key_pc), None, mode)
    return plan
