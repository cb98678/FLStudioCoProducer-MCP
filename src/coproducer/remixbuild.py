"""Build the remix project from the plan loaded into `remixplan`: editable drums, bass, stabs and vocal chops as patterns, the stretched vocal and an FX bed as
playlist audio. Behind tools/build_techhouse.py and the module build_remix_project. The inputs are never written; the output must sit under a folder named sandbox.
"""
from __future__ import annotations

import json
import os
from typing import Callable

from . import drumplan, flpfile, partmix, projorg, remixplan

TPB = flpfile.TICKS_PER_BEAT
KIT = {  # plan instrument -> (channel name, sample file, mixer group)
    "kick": ("Kick", "CP_Kick.wav", "kick"), "snare": ("Snare", "CP_Snare.wav", "clap"), "clap": ("Clap", "CP_Clap.wav", "clap"),
    "hat": ("Closed Hat", "CP_HatC.wav", "hats"), "ohat": ("Open Hat", "CP_HatO.wav", "hats"), "shaker": ("Shaker", "CP_Shaker.wav", "hats"),
    "rim": ("Rim", "CP_Rim.wav", "perc"), "tom": ("Tom", "CP_Tom.wav", "perc"), "crash": ("Crash", "CP_Crash.wav", "perc"),
    "perc": ("Perc", "CP_Perc.wav", "perc"), "ride": ("Ride", "CP_Ride.wav", "hats"),
}
OPTIONAL_VOICES = ("perc", "ride")  # channels only when the drum plan plays them (the demo study's grooves), so older plans build as before
INSTRUMENT_PARTS = {"stab": "stab", "arp": "arp", "sub": "sub", "bass": "reese"}  # variety sound role -> the build's part
PART_WORD = {"reese": "Bass", "stab": "Stab", "arp": "Arp", "sub": "Sub"}            # the word an imported channel's name starts with when its label has none
PART_ROLES = {"reese": ("reese", "bass"), "stab": ("stab",), "arp": ("arp",), "sub": ("sub",)}
# The person's own sounds won over the generated ones (approved tech-house v15, 2026-10-24); the generated stab and arp stay reachable with serum_preset
# The chord synth: "PL Crusty Pluck [LCV]" from the person's own edit of the techno remix (2026-10-26), where it replaced "Cowbell - Keep Calm"
# and sat 3.5 dB lower; the old one stays reachable with serum_preset stab="Cowbell - Keep Calm".
SERUM_PRESETS = {"sub": "CP - Deep Sub", "stab": "PL Crusty Pluck [LCV]", "arp": "ARP - Jno Style"}
SERUM_DB = {"sub": -6.5, "stab": -2.5, "arp": -4.0, "pad": -6.0}  # the person's levels where they set them; the part-level loop (tools/part_levels.py) replaces them
SERUM_SUB_OFFSET = 7  # the Sytrus Remix Sub patch needs key = MIDI + 7; Serum plays at true pitch
SYNTHS = (("sub", "Sub Bass", "Remix Sub"), ("stab", "Chord Stab", "Trance pluck"), ("arp", "Rising Arp", "Trance pluck #2"),
          ("pad", "Pad", "Trance pluck"))   # the pad: a generated Serum sound when there is one; the pluck patch is only a stand-in
ROW = {"fx": 0, "vocal": 1, "drums": 2, "reese": 3, "sub": 4, "stab": 5, "arp": 6, "chops": 7, "orig": 8, "pad": 9}  # playlist rows, top to bottom (0-based)


class BuildError(ValueError):
    """A bad argument or a missing channel; the message says which."""


def find_channel(f: flpfile.Flp, name: str) -> int:
    for c in f.channel_ids():
        if f.get_text(c, flpfile.EV_CH_NAME) == name:
            return c
    raise BuildError("channel %r not found" % name)


def find_stem_channel(f: flpfile.Flp, stem: str = "vocals") -> int:
    """The base project's channel holding the stem audio (its name ends with the stem name, e.g. song_vocals)."""
    hits = [c for c in f.channel_ids() if (f.channel_info(c)["name"] or "").lower().endswith(stem)]
    if not hits:
        raise BuildError("no channel whose name ends with %r in the base project" % stem)
    return hits[0]


def pairs(items: list[str] | dict | None, allowed, label: str, cast=str) -> dict:
    """KEY=VALUE strings (or a dict) checked against the allowed keys."""
    out = {}
    for item in (items.items() if isinstance(items, dict) else [i.partition("=")[::2] for i in (items or [])]):
        k, v = item
        if k not in allowed or v in ("", None):
            raise BuildError("%s wants KEY=VALUE with KEY one of %s" % (label, ", ".join(allowed)))
        out[k] = cast(v)
    return out


def _vocal_clips(meta: dict, origin: float, stem: str = "vocals") -> list[tuple]:
    """Playlist positions of the plan's long clips of one stem: (position, length in ticks, start ms, end ms in the stretched file). Each clip's
    source bar line lands on its remix bar, so a pickup sung before the bar line starts before it."""
    bar_s, spt = 240.0 / remixplan.BPM, 60.0 / remixplan.BPM / TPB
    ratio, delay = meta["stretch"], meta["delay_s"]
    out = []
    for (remix_bar, orig_bar, *_h), clip in zip(remixplan.VOCAL_CLIPS, meta["clips"]):
        if clip.get("stem", "vocals") != stem:
            continue
        s0, s1 = clip["orig_start_s"] / ratio + delay, clip["orig_end_s"] / ratio + delay
        anchor = (origin + orig_bar * 240.0 / remixplan.SOURCE_BPM) / ratio + delay  # stretched time of the original bar line
        out.append((round((remix_bar * bar_s + s0 - anchor) / spt), round((s1 - s0) / spt), s0 * 1000.0, s1 * 1000.0))
    return out


def start_db(grp: str, default: float, serum: bool, serum_levels: dict, style: dict | None) -> float:
    """A mixer group's starting level: the style's own (the person's approved balance for that style, e.g. the Curse of Curves house master
    B), else the Serum sound's level when Serum plays it, else the song-form default, else the group default."""
    own = (style or {}).get("levels_db", {})
    if grp in own:
        return float(own[grp])
    if serum and grp in serum_levels:
        return float(serum_levels[grp])
    return float(remixplan.SONG_FORM_DB.get(grp, default) if remixplan.DIATONIC else default)


def chop_phase(meta: dict, name: str) -> float:
    """Remix beats to delay a chop so the song's own beat grid inside it lands on the remix's beats. A chop starts on its first word, which
    is rarely on a beat (the Curse of Curves hook starts 0.44 of a beat before one): placed on a beat, everything in it sat off the beat,
    and the person moved every chop later by about that much (2026-10-26). Echoes take their dry chop's phase."""
    c = meta["chops"].get(name[:-5] if name.endswith("_echo") else name, {})
    if "orig_start_s" not in c:
        return 0.0
    beat = 60.0 / remixplan.SOURCE_BPM
    ph = ((c["orig_start_s"] - remixplan.ORIGIN_S) / beat) % 1.0
    ph = 0.0 if ph > 0.95 or ph < 0.05 else ph  # on a beat already
    return round(ph / remixplan.VOCAL_MULTIPLE, 4)


def stutter_clips(meta: dict, stutter: tuple) -> list[tuple]:
    """(position, length in ticks, start ms, end ms) for each hit of the roll: the stutter chop's slice of the stretched vocal, cut shorter
    with each hit (a clip plays only its own length, so the hits never smear into each other)."""
    name, bars, hits = stutter
    c = meta["chops"][name]
    ratio, delay = meta["stretch"], meta["delay_s"]
    s0, s1 = c["orig_start_s"] / ratio + delay, c["orig_end_s"] / ratio + delay
    bar_t, spt = 4 * TPB, 60.0 / remixplan.BPM / TPB
    out = []
    for b in bars:
        for start, length in hits:
            ln = min(length * bar_t, (s1 - s0) / spt)
            out.append((round(b * bar_t + start * bar_t), max(1, round(ln)), s0 * 1000.0, (s0 + ln * spt) * 1000.0))
    return out


def _overlaps(meta: dict, vclips: list[tuple]) -> list[str]:
    spt = 60.0 / remixplan.BPM / TPB
    dry = {n: v["dur_s"] for n, v in meta["chops"].items() if not n.endswith("_echo")}
    full = dict(dry)
    for n in remixplan.ECHOED:
        dry[n + "_echo"], full[n + "_echo"] = dry[n], meta["chops"][n + "_echo"]["dur_s"]
    voc = [c for c, m in zip(remixplan.VOCAL_CLIPS, meta["clips"]) if m.get("stem", "vocals") == "vocals"]
    spans = [(c[4], p * spt, (p + ln) * spt) for c, (p, ln, *_r) in zip(voc, vclips)]
    return remixplan.chop_conflicts(remixplan.chop_events(), dry, full, extra=spans)


def marker_names(sections: list[dict]) -> list[str]:
    """Section names for time markers, numbered where a name repeats (Drop 1, Drop 2), so a marker name finds one moment."""
    total = {}
    for sec in sections:
        total[sec["name"]] = total.get(sec["name"], 0) + 1
    seen: dict[str, int] = {}
    out = []
    for sec in sections:
        seen[sec["name"]] = seen.get(sec["name"], 0) + 1
        label = sec["name"].replace("_", " ").title()
        name = label if total[sec["name"]] == 1 else "%s %d" % (label, seen[sec["name"]])
        out.append("%s: %s" % (name, sec["label"]) if sec.get("label") else name)  # "Break 2: Mid 8" still reads as a break downstream
    return out


def add_section_markers(f: flpfile.Flp, sections: list[dict]) -> list[str]:
    """A time marker at the start of each section (bars count from 0 in the plan). A marker already at that bar with that name is kept as is."""
    have = {(m["pos"], m["name"]) for m in f.time_markers()}
    names = marker_names(sections)
    for sec, name in zip(sections, names):
        pos = int(sec["start"]) * TPB * 4
        if (pos, name) not in have:
            f.add_time_marker(pos, name)
    return names


def serum_channels(sfile, presets: dict, states: dict, log: Callable[..., None] = print) -> tuple[dict, dict]:
    """({part: channel id in the Serum project}, {part: plugin state bytes}). A part with a generated sound (states: part -> a file written
    by render_serum_sound, a Serum 2 channel state) takes any Serum 2 channel of the project as its carrier and gets that state; the
    other parts are matched by preset name."""
    from . import serumstate
    if sfile is None:
        return {}, {}
    by_name = {sfile.plugin_preset_name(c): c for c in sfile.channel_ids() if sfile.plugin_preset_name(c)}
    chans = {k: by_name[n] for k, n in presets.items() if n in by_name}
    carriers = [c for c in sfile.channel_ids() if serumstate.is_serum2(sfile.plugin_state(c) or b"")]
    blobs = {}
    for part, path in (states or {}).items():
        if not carriers:
            raise BuildError("no Serum 2 channel in the Serum project to carry the generated %s sound" % part)
        with open(path, "rb") as fh:
            blob = fh.read()
        if not serumstate.is_serum2(blob):
            raise BuildError("%s is not a Serum 2 channel state" % path)
        chans.setdefault(part, carriers[0])
        blobs[part] = blob
        log("serum generated sound:", part, serumstate.preset_name(blob))
    return chans, blobs


def demo_instrument(entry: dict, demo_dir: str) -> tuple[flpfile.Flp, list[int]] | None:
    """(project, channel ids) for a plan instrument {"import": {"flp", "channels", "path"?}}: the demo song's render copy (demo_dir/FLP.flp,
    or the entry's own path) and the channels of the instrument that it really has. None when the file or the channels are missing."""
    imp = entry.get("import") or {}
    path = imp.get("path") or (os.path.join(demo_dir, imp.get("flp", "") + ".flp") if demo_dir and imp.get("flp") else "")
    if not path or not os.path.isfile(path):
        return None
    src = flpfile.Flp.load(path)
    have = set(src.channel_ids())
    chans = [c for c in imp.get("channels", []) if c in have][:3]
    return (src, chans) if chans else None


def _midi(name: str | None) -> int | None:
    import re
    m = re.match(r"^([A-G])([#b]?)(-?\d+)$", name or "")
    if not m:
        return None
    pc = "C C# D D# E F F# G G# A A# B".split().index(m.group(1) + ("#" if m.group(2) == "#" else "")) - (1 if m.group(2) == "b" else 0)
    return 12 * (int(m.group(3)) + 1) + pc


def register_shift(notes: list[tuple], register) -> int:
    """Octaves (in semitones) that move a part's notes so their middle sits in the demo instrument's own register (its lowest and highest
    note names), so an imported synth plays where its designer played it."""
    if not notes or not register:
        return 0
    lo, hi = _midi(register[0]), _midi(register[-1])
    if lo is None or hi is None:
        return 0
    keys = sorted(n[2] for n in notes)
    mid = keys[len(keys) // 2]
    return 12 * round(((lo + hi) / 2.0 - mid) / 12.0)


def blocks(sections: list[dict], most: int) -> list[tuple[int, int, str]]:
    """(start bar, bars, name) piano-roll blocks: each section cut into pieces of at most `most` bars, named by its marker ("Drop 2", then
    "Drop 2 b" for its second piece). Empty for most 1 (one pattern per distinct bar, the older layout)."""
    if most <= 1:
        return []
    out = []
    for s, name in zip(sections, marker_names(sections)):
        for k, a in enumerate(range(s["start"], s["end"], most)):
            out.append((a, min(most, s["end"] - a), name if k == 0 else "%s %s" % (name, "bcdefgh"[min(k - 1, 6)])))
    return out


def build(base: str, dtp: str, audio: str, out: str, *, origin: float | None = None, serum: str = "", serum_preset=None, serum_db=None, kit=None,
          stab_offbeat: bool = False, solo: str = "", organize: bool = True, serum_state=None, demo_dir: str = "", log: Callable[..., None] = print) -> dict:
    """Write the remix project `out` and return a report: channel ids, pattern counts, vocal clip positions and the chop overlap notes.

    The plan loaded in remixplan may carry a kit (KIT_PATHS: voice to sample path, a demo song's kit) and instruments (INSTRUMENTS: part
    to a demo song's channel): a part with a generated Serum sound keeps it, a part without one plays the demo instrument, imported from
    the demo's render copy in demo_dir, its notes moved into the instrument's own register."""
    if "sandbox" not in [p.lower() for p in os.path.abspath(out).split(os.sep)]:
        raise BuildError("refusing to write %s: output must be under a folder named sandbox" % out)
    origin = remixplan.ORIGIN_S if origin is None else origin
    presets = {**SERUM_PRESETS, **pairs(serum_preset, SERUM_PRESETS, "serum_preset")}
    levels = {**SERUM_DB, **pairs(serum_db, SERUM_DB, "serum_db", float)}
    kit_over = {**{k: v for k, v in (remixplan.KIT_PATHS or {}).items() if k in KIT}, **pairs(kit, KIT, "kit")}
    with open(os.path.join(audio, "techhouse_audio.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    audio = os.path.abspath(audio)
    f, sytrus = flpfile.Flp.load(base), flpfile.Flp.load(dtp)
    sfile = flpfile.Flp.load(serum) if serum else None
    serum_ch, serum_blobs = serum_channels(sfile, presets, serum_state, log)
    if sfile:
        log("serum channels:", {k: presets.get(k, "generated") for k in serum_ch}, "missing:", [k for k in presets if k not in serum_ch])
    sampler_src, audio_src = f.channel_ids()[0], find_stem_channel(f, "vocals")
    vocal_tmpl, old = f.audio_item(audio_src), list(f.channel_ids())
    ids: dict[str, int] = {}
    group_of: dict[int, str] = {}

    def new_channel(key: str, name: str, group: str, *, sample: str | None = None, source: flpfile.Flp | None = None, src: int | None = None) -> None:
        nid = max(old + list(ids.values())) + 1
        track = remixplan.GROUPS[group][0]
        if source is None:
            f.clone_channel(src if src is not None else sampler_src, nid, name, track)
        else:
            f.import_channel(source, src, nid, name, track)
        if sample:
            f.set_sample(nid, os.path.join(audio, sample), name)
        if key in kit_over:
            f.set_sample(nid, kit_over[key], os.path.splitext(kit_over[key].replace("\\", "/").rsplit("/", 1)[-1])[0])
        ids[key], group_of[nid] = nid, group

    style = remixplan.STYLE
    skip: set[str] = set()
    if style:  # a grammar style: parts with no notes get no channel (techno has no sub line, dubstep no stabs)
        dp = remixplan.drums()
        lines = {"reese": remixplan.reese_notes(), "sub": remixplan.sub_notes(dp), "stab": remixplan.stab_notes(), "arp": remixplan.arp_notes()}
        skip = {k for k, v in lines.items() if not v}
    if not remixplan.pad_notes():   # the pad is its own part only when the chords option has a pad layer
        skip.add("pad")
    used = {e[2] for e in remixplan.drums().events}
    for inst, (name, file, grp) in KIT.items():
        if inst in OPTIONAL_VOICES and inst not in used:
            continue
        if inst not in kit_over and not os.path.isfile(os.path.join(audio, file)):  # an audio folder prepared before the voice existed
            from . import oneshots
            oneshots.write_wav(os.path.join(audio, file), oneshots.KIT[file[:-4]]())
        new_channel(inst, name, grp, sample=file)
    imported: dict[str, dict] = {}
    for role, entry in (remixplan.INSTRUMENTS or {}).items():
        part = INSTRUMENT_PARTS.get(role)
        if not part or part in skip or part in serum_blobs:
            continue
        got = demo_instrument(entry, demo_dir)
        if got:
            imported[part] = {"src": got[0], "channels": got[1], "label": entry.get("label") or part, "register": entry.get("register")}
        else:
            log("instrument for %s not imported (no render copy of %s in %s)" % (part, (entry.get("import") or {}).get("flp"), demo_dir or "-"))
    extra: dict[str, list[str]] = {}

    def import_stack(part: str, label: str) -> None:
        imp = imported[part]
        if partmix.role_of(label) not in PART_ROLES[part]:   # "DX10 log drum" names no role: routing, pumps and section gains go by role
            label = "%s - %s" % (PART_WORD[part], label)
        for k, ch in enumerate(imp["channels"]):
            key = part if k == 0 else "%s_layer%d" % (part, k)
            new_channel(key, label if k == 0 else "%s %d" % (label, k + 1), part, source=imp["src"], src=ch)
            if k:
                extra.setdefault(part, []).append(key)
    if "reese" not in skip:
        if "reese" in imported:
            import_stack("reese", imported["reese"]["label"])
        else:
            new_channel("reese", (style or {}).get("bass_sample", {}).get("label", "Reese Bass"), "reese", sample="CP_Reese.wav")
    for key, label, sytrus_name in SYNTHS:
        if key in skip:
            continue
        if key in imported:
            import_stack(key, imported[key]["label"])
        elif key in serum_ch:
            new_channel(key, label, key, source=sfile, src=serum_ch[key])
            if key in serum_blobs:
                f.set_plugin_state(ids[key], serum_blobs[key])
        else:
            new_channel(key, label, key, source=sytrus, src=find_channel(sytrus, sytrus_name))
    for name in meta["chops"]:
        new_channel("chop_" + name, "Chop " + name, "chops", sample=meta["chops"][name]["file"])
    vlabel = "Vocal %d bpm" % round(remixplan.BPM) if remixplan.VOCAL_MULTIPLE == 1 else "Vocal %d bpm (x%g)" % (round(remixplan.BPM * remixplan.VOCAL_MULTIPLE), remixplan.VOCAL_MULTIPLE)
    new_channel("vocal", vlabel, "vocal", sample="vocals_%d.wav" % round(remixplan.BPM), src=audio_src)
    new_channel("fx", "FX bed", "fx", sample="FX_bed.wav", src=audio_src)
    if any(c.get("stem") == "other" for c in meta["clips"]):  # the original's own instrumentation, on its own channel and insert
        new_channel("orig", "Original Instruments", "orig", sample="other_%d.wav" % round(remixplan.BPM), src=audio_src)
    f.strip_notes(set(old))  # drop the stem project's own channels, notes and clips
    f.clear_playlist()
    for c in old:
        f.remove_channel(c)
    f.set_tempo(remixplan.BPM)
    f.set_song_mode(True)  # the stem project is in pattern mode, where a render covers one pattern only

    plan = remixplan.drums()
    spans = blocks(remixplan.SECTIONS, remixplan.PATTERN_BARS)

    def place(label: str, by_bar: dict[int, bytes], row: int) -> int:
        """Patterns and clips for one part: a piano roll per section (up to PATTERN_BARS bars) or one pattern per distinct bar."""
        got = f.add_part_blocks(label, by_bar, row, f.next_pattern_id(1), spans) if spans else f.add_part(label, by_bar, row, f.next_pattern_id(1))
        return len(set(got.values()))
    parts = {"Drums": place("Drums", drumplan.to_note_bytes(plan, {i: ids[i] for i in KIT if i in ids}), ROW["drums"])}
    shifts: dict[str, int] = {}

    def add(label: str, key: str, notes: list[tuple]) -> None:
        if key in skip:
            return
        if key in imported:  # the demo instrument plays at true pitch, in its own register
            if key in ("sub",):
                notes = [(n[0], n[1], n[2] - SERUM_SUB_OFFSET, *n[3:]) for n in notes]
            elif key == "reese":
                notes = [(n[0], n[1], n[2] - 60 + 33, *n[3:]) for n in notes]   # the reese sampler's key 60 is A1 (MIDI 33)
            shifts[key] = register_shift(notes, imported[key]["register"])
            notes = [(n[0], n[1], n[2] + shifts[key], *n[3:]) for n in notes]
        parts[label] = place(label, flpfile.notes_by_bar(notes, ids[key]), ROW[key])
        for k, lay in enumerate(extra.get(key, [])):
            parts["%s layer %d" % (label, k + 2)] = place("%s %d" % (label, k + 2), flpfile.notes_by_bar(notes, ids[lay]), ROW[key])

    sub = remixplan.sub_notes(plan)
    add("Reese", "reese", remixplan.reese_notes())
    add("Sub", "sub", [(n[0], n[1], n[2] - SERUM_SUB_OFFSET, *n[3:]) for n in sub] if "sub" in serum_ch and "sub" not in imported else sub)
    add("Stabs", "stab", remixplan.stab_notes(offbeat=stab_offbeat))
    add("Arp", "arp", remixplan.arp_notes())
    add("Pad", "pad", remixplan.pad_notes())
    phase = {n: chop_phase(meta, n) for n in meta["chops"]}
    rows = [(max(0.0, bar * 4 + step / 4 + phase.get(name, 0.0)), 0, key, vel, ids["chop_" + name]) for bar, step, name, vel, key in remixplan.chop_events()]
    parts["Chops"] = place("Chops", flpfile.notes_by_bar_channels(rows), ROW["chops"])
    vclips = _vocal_clips(meta, origin)
    f.add_audio_clips(ids["vocal"], ROW["vocal"], vclips, vocal_tmpl)
    notes = _overlaps(meta, vclips)
    if remixplan.STUTTER and remixplan.STUTTER[0] in meta["chops"]:
        f.add_audio_clips(ids["vocal"], ROW["vocal"], stutter_clips(meta, remixplan.STUTTER), vocal_tmpl)
    f.add_audio_clips(ids["fx"], ROW["fx"], [(0, (remixplan.TOTAL_BARS + 2) * 4 * TPB, -1.0, -1.0)], vocal_tmpl)  # +2 bars: the last downlifter's tail
    if "orig" in ids:
        f.add_audio_clips(ids["orig"], ROW["orig"], _vocal_clips(meta, origin, "other"), vocal_tmpl)
    if solo:
        keep = set(solo.split(","))
        for ch, grp in group_of.items():
            if grp not in keep:
                f.set_enabled(ch, False)
    for grp, (track, db) in remixplan.GROUPS.items():
        f.set_mixer_volume(track, remixplan.fader_raw(start_db(grp, db, grp in serum_ch, levels, style)))
    f.set_mixer_volume(0, remixplan.fader_raw(remixplan.MASTER_DB))
    mapping = f.renumber_channels()  # ids 0..n-1: FL shows any gap as a blank sampler
    markers = add_section_markers(f, remixplan.SECTIONS)  # FL shows the sections; transition and section tools find them by name
    if organize:  # house names, colours and groups (docs/PROJECT_STANDARD.md), so every build looks the same
        projorg.apply(f, projorg.plan(f))
    f.save(out)
    g = flpfile.Flp.load(out)
    return {"out": out, "tempo": g.tempo(), "channels": g.channel_count, "patterns": len(g.pattern_ids()), "playlist_items": len(g.playlist_items()),
            "pattern_counts": parts, "chop_phase_beats": phase, "vocal_clips": vclips, "channel_ids": {k: mapping[v] for k, v in ids.items()}, "overlap_notes": notes, "serum": sorted(serum_ch), "serum_generated": sorted(serum_blobs),
            "markers": markers, "kit": sorted(kit_over), "imported": {k: {"label": v["label"], "channels": v["channels"], "shift": shifts.get(k, 0)} for k, v in imported.items()}}
