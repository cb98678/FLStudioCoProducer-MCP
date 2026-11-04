"""A song plan as one JSON document: everything about the song that the remix recipe needs, so the recipe itself holds no song.

The recipe code (remixplan, drumplan, tension, arrange) reads module values; `apply` sets them from a plan, `export_current` writes the values now loaded
(the first song's plan is what remixplan ships with). A plan from song analysis fills the same fields (docs/STEM_REMIX_PIPELINE.md).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import arrange, flpfile, remixplan, stylepack

REQUIRED = ("name", "bpm", "source_bpm", "key_pc", "origin_s", "roots8", "sections", "chops", "echoed", "vocal_clips", "clip_words")
SECTION_NAMES = ("intro", "groove", "break", "build", "drop", "outro")
SCOOP_WHEN = ("phrase", "long", "phrase_or_long", "all", "none")  # remixplan.sampler_lead_notes: which notes of a sampled lead bend in
STEMS = ("vocals", "other")  # long clips play the vocal stem or the original's instrumentation (Demucs "other": guitars, keys, strings)


class PlanError(ValueError):
    """Raised for a plan that cannot drive a build; the message says which field."""


def drum_loops(plan: dict) -> list[dict]:
    """A plan's captured drum loops: "drum_loops" (a list), or "drum_loop" for one."""
    return list(plan.get("drum_loops") or ([plan["drum_loop"]] if plan.get("drum_loop") else []))


def validate(plan: dict) -> list[str]:
    """Problems with a plan, one sentence each; an empty list means it can drive a build."""
    bad = ["missing field: " + k for k in REQUIRED if k not in plan]
    if bad:
        return bad
    out = []
    if not 60 <= plan["bpm"] <= 200 or not 40 <= plan["source_bpm"] <= 240:
        out.append("tempo out of range")
    if len(plan["roots8"]) != 8 or any(not 0 <= p < 12 for p in plan["roots8"]):
        out.append("roots8 must be 8 pitch classes 0..11")
    if plan.get("pattern_bars", 1) not in (1, 2, 4, 8, 16):
        out.append("pattern_bars must be 1, 2, 4, 8 or 16")
    prev = 0
    for s in plan["sections"]:
        if s["name"] not in SECTION_NAMES:
            out.append("unknown section name %r" % s["name"])
        if s["start"] != prev or s["end"] <= s["start"]:
            out.append("section %r does not continue from bar %d" % (s["name"], prev))
        prev = s["end"]
    for n, spec in plan["chops"].items():
        if not 0 <= spec["start"] < spec["end"]:
            out.append("chop %s has a bad time window" % n)
    for n in plan["echoed"]:
        if n not in plan["chops"]:
            out.append("echoed chop %s is not in chops" % n)
    if len(plan["clip_words"]) != len(plan["vocal_clips"]):
        out.append("clip_words and vocal_clips differ in length")
    for c in plan["vocal_clips"]:
        if len(c) not in (6, 7) or c[5] not in ("word", "phrase", "bars") or (len(c) == 7 and c[6] not in STEMS):
            out.append("vocal clip %r: [remix bar, orig bar, start, end, label, word|phrase|bars, stem (vocals or other)]" % (c[4] if len(c) > 4 else c))
    sp = plan.get("bar_splits8")
    if sp is not None and (len(sp) != 8 or any(x is not None and (len(x) != 2 or not 1 <= x[0] <= 15 or not 0 <= x[1] < 12) for x in sp)):
        out.append("bar_splits8 must hold 8 entries, each null or [16th step 1..15, pitch class]")
    roots = plan.get("bar_roots")
    if roots is not None and (len(roots) != plan["sections"][-1]["end"] or any(r is not None and not 0 <= r < 12 for r in roots)):
        out.append("bar_roots must hold one pitch class or null per bar of the song")
    if "roles" in plan and arrange.missing_roles(plan["roles"]):
        out.append("chop roles missing: " + ", ".join(arrange.missing_roles(plan["roles"])))
    if plan.get("style") and plan["style"] not in stylepack.names():
        out.append("unknown style %r (known: %s)" % (plan["style"], ", ".join(stylepack.names())))
    elif plan.get("style") and plan.get("style_overrides"):
        from . import variety
        try:
            out += ["style_overrides: " + x for x in stylepack.validate(variety.apply_overrides(stylepack.load(plan["style"]), plan["style_overrides"]))]
        except (KeyError, TypeError, ValueError) as e:
            out.append("style_overrides do not apply: %s" % e)
    if plan.get("mode", "major") not in ("major", "minor"):
        out.append("mode must be major or minor")
    for v in (plan.get("kit") or {}):
        if v not in stylepack.VOICES:
            out.append("kit voice %r is not a drum voice" % v)
    if not 0.25 <= float(plan.get("vocal_multiple", 1.0)) <= 4:
        out.append("vocal_multiple out of range")
    elif float(plan["bpm"]) * float(plan.get("vocal_multiple", 1.0)) / float(plan["source_bpm"]) < stylepack.MAX_SLOWDOWN - 1e-9:
        out.append("the vocal would run more than %.0f%% slower than it was sung (bpm x vocal_multiple against source_bpm); the rule is its own"
                   " tempo, faster, or at most that much slower with its pitch kept" % (100 * (1 - stylepack.MAX_SLOWDOWN)))
    st = plan.get("stutter")
    if st is not None and (st.get("chop") not in plan["chops"] or any(not 0 <= int(b) < plan["sections"][-1]["end"] for b in st.get("bars", []))
                           or any(len(h) != 2 or not 0 <= h[0] < 1 or not 0 < h[1] <= 1 for h in st.get("hits", []))):
        out.append("stutter: {chop (a chop name), bars (remix bars), hits ([start, length] in bars, inside the bar)}")
    if plan.get("vocal_stretch", "rubberband") not in ("rubberband", "fl"):
        out.append("vocal_stretch must be rubberband or fl")
    if any(k not in STEMS or v not in flpfile.STRETCH_MODES for k, v in (plan.get("fl_stretch_modes") or {}).items()):
        out.append("fl_stretch_modes: {vocals or other: a flpfile.STRETCH_MODES name}")
    if any(k not in STEMS or not -1200 <= int(v) <= 1200 for k, v in (plan.get("fl_pitch_cents") or {}).items()):
        out.append("fl_pitch_cents: {vocals or other: cents within an octave}")
    if any(len(x) != 2 or not 0 <= float(x[0]) < float(x[1]) for x in (plan.get("band_rests") or [])):
        out.append("band_rests: [[start beat, end beat], ...] with start before end")
    for b, ch in (plan.get("chord_map") or {}).items():
        if not str(b).lstrip("-").isdigit() or any(len(x) != 2 or not 0 <= int(x[0]) <= 15 or not 0 <= int(x[1]) < 12 for x in ch):
            out.append("chord_map: {bar: [[16th step 0..15, pitch class 0..11], ...]}")
            break
    sl = plan.get("sampler_lead")
    if sl:
        if not sl.get("sample") or not 0 <= float(sl.get("root_midi", 60)) <= 127:
            out.append("sampler_lead needs a sample (WAV path) and its root_midi (the note it sounds, 0..127)")
        if any(len(n) not in (3, 4) or float(n[1]) <= 0 or not 0 <= int(n[2]) <= 127 for n in sl.get("notes") or ()):
            out.append("sampler_lead notes are [start beat, length beats, MIDI note, velocity]")
        if (sl.get("scoop") or {}).get("when", "phrase") not in SCOOP_WHEN:
            out.append("sampler_lead scoop when must be one of " + ", ".join(SCOOP_WHEN))
    bs = plan.get("bass_sample")
    if bs and (not bs.get("file") or not 0 <= float(bs.get("root_midi", -1)) <= 127):
        out.append("bass_sample needs a file (one bass note, WAV) and its root_midi")
    for dl in drum_loops(plan):
        if not dl.get("sample") or int(dl.get("bars", 1)) not in (1, 2, 4, 8):
            out.append("a drum loop needs a sample (a loop cut to the remix tempo) and bars 1, 2, 4 or 8")
    if "chop_events" not in plan and "roles" not in plan:
        out.append("need chop_events or roles to place the chops")
    for row in plan.get("chop_events", []):
        if row[2] not in plan["chops"] and row[2].rsplit("_echo", 1)[0] not in plan["chops"]:
            out.append("chop_events names unknown chop %s" % row[2])
    return out


def export_current(name: str = "friends_in_low_places") -> dict:
    """The plan the recipe module currently holds, as a JSON-ready dict."""
    return {"name": name, "bpm": remixplan.BPM, "source_bpm": remixplan.SOURCE_BPM, "key_pc": remixplan.KEY_PC, "origin_s": 27.3085, "roots8": list(remixplan.ROOTS8),
            "sections": [dict(s) for s in remixplan.SECTIONS], "chops": {k: dict(v) for k, v in remixplan.CHOPS.items()}, "echoed": list(remixplan.ECHOED),
            "vocal_clips": [list(c) for c in remixplan.VOCAL_CLIPS], "clip_words": [dict(c) for c in remixplan.CLIP_WORDS],
            "chop_events": [list(e) for e in remixplan.chop_events()], "fx_cues": remixplan.fx_cues(), "roles": dict(remixplan.FRIENDS_ROLES),
            "pitch_ratio": remixplan.PITCH_RATIO}


def apply(plan: dict) -> None:
    """Load a plan into the recipe module. Raises PlanError listing every problem if the plan is not usable."""
    problems = validate(plan)
    if problems:
        raise PlanError("; ".join(problems))
    r = remixplan
    r.BPM, r.SOURCE_BPM, r.KEY_PC = float(plan["bpm"]), float(plan["source_bpm"]), int(plan["key_pc"])
    r.VOCAL_MULTIPLE = float(plan.get("vocal_multiple", 1.0))
    r.PITCH_RATIO = float(plan.get("pitch_ratio", 1.0))
    r.STRETCH = r.BPM * r.VOCAL_MULTIPLE / r.SOURCE_BPM
    pack = stylepack.load(plan["style"]) if plan.get("style") else None
    if pack and plan.get("style_overrides"):  # the song's own choices from the variety bank (form, groove, bass, chords, arp)
        from . import variety
        pack = variety.apply_overrides(pack, plan["style_overrides"])
    r.STYLE = pack if pack and pack["engine"] == "grammar" else None
    r.MODE = plan.get("mode", "major")
    r.ROOT_QUALITY = {int(k): v for k, v in (plan.get("root_quality") or {}).items()}
    r.KIT_PATHS = dict(plan.get("kit") or {})
    r.INSTRUMENTS = {k: dict(v) for k, v in (plan.get("instruments") or {}).items()}
    r.ROOTS8 = tuple(plan["roots8"])
    r.BAR_ROOTS = tuple(plan.get("bar_roots") or ())
    r.BAR_SPLITS = tuple(tuple(x) if x else None for x in plan.get("bar_splits8") or ())
    r.DIATONIC = plan.get("arrangement") == "song"
    r.KEYS_NOTES = tuple(tuple(n) for n in plan.get("keys_notes") or ())
    r.LEAD_NOTES = tuple(tuple(n) for n in plan.get("lead_notes") or ())
    r.PATTERN_BARS = int(plan.get("pattern_bars", 1))
    r.VOCAL_STRETCH = plan.get("vocal_stretch", "rubberband")
    r.FL_STRETCH_MODES = {str(k): str(v) for k, v in (plan.get("fl_stretch_modes") or {}).items()}
    r.FL_PITCH_CENTS = {str(k): int(v) for k, v in (plan.get("fl_pitch_cents") or {}).items()}
    r.CHORD_MAP = {int(b): sorted((int(st), int(pc)) for st, pc in ch) for b, ch in (plan.get("chord_map") or {}).items()}
    r.SAMPLER_LEAD = dict(plan.get("sampler_lead") or {})
    r.DRUM_LOOPS = [dict(x) for x in drum_loops(plan)]
    r.BASS_SAMPLE = dict(plan.get("bass_sample") or {})
    r.BASS_SAMPLE_PC = int(round(float(r.BASS_SAMPLE["root_midi"]))) % 12 if r.BASS_SAMPLE else 9
    r.SECTIONS = [dict(s) for s in plan["sections"]]
    r.TOTAL_BARS = r.SECTIONS[-1]["end"]
    r.CHOPS = {k: dict(v) for k, v in plan["chops"].items()}
    r.ECHOED = tuple(plan["echoed"])
    r.VOCAL_CLIPS = [tuple(c) for c in plan["vocal_clips"]]
    r.CLIP_WORDS = [dict(c) for c in plan["clip_words"]]
    r.ORIGIN_S = float(plan["origin_s"])
    r.CHOP_EVENTS_OVERRIDE = [tuple(e) for e in plan["chop_events"]] if "chop_events" in plan else None
    r.CHOP_ROLES = dict(plan["roles"]) if "roles" in plan else None
    r.FX_CUES_OVERRIDE = list(plan["fx_cues"]) if "fx_cues" in plan else None
    r.BAND_RESTS = [[float(a), float(b)] for a, b in (plan.get("band_rests") or [])]
    st = plan.get("stutter")
    r.STUTTER = (st["chop"], tuple(int(b) for b in st["bars"]), tuple(tuple(h) for h in st["hits"])) if st else None


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(plan: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8")
