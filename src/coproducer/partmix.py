"""Set part levels from solo renders instead of by guess.

A project is split into one solo project per mixer track (every channel on other tracks disabled). FL renders them all in one launch (`/F`), each
render is measured, and the measured level of each part, relative to the kick, is compared with a profile taken from a mix the person approved.
The difference is the fader change (capped per pass, spec F-04). The profile is the person's taste (V1) captured as numbers; no target is invented here.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from . import anatomy, dsp, flpfile
from .automation import db_to_fader, fader_to_db

ROLE_WORDS = (  # first match wins; a word matches a lower-case name token that equals it (or starts with it when the word has 4+ letters)
    ("orig", ("original",)), ("chops", ("chop", "chops", "slice")), ("kick", ("kick", "bd")), ("clap", ("clap", "snare", "snr")),
    ("hats", ("hat", "hats", "ch", "oh", "hh", "shaker", "ride")), ("perc", ("rim", "tom", "perc", "crash", "cowbell", "conga")),
    ("reese", ("reese",)), ("sub", ("sub",)), ("bass", ("bass", "808")), ("arp", ("arp", "pluck", "lead")),   # an 808 alone is the bass ("808 Kick": kick first)
    ("stab", ("stab", "chord", "pad", "keys", "piano")), ("vocal", ("vocal", "vox", "acapella")), ("fx", ("fx", "riser", "impact", "sweep", "sfx", "downlifter", "uplifter", "noise")),
    ("synth", ("synth",)),
)
MAX_STEP_DB = 12.0  # most one pass may move a fader
TOLERANCE_DB = 1.0
FADER_MAX_DB = 5.5  # the mixer fader tops out at +5.6 dB; a part that needs more has to be raised at the instrument


def role_of(name: str) -> str | None:
    """The part role a channel or insert name says. A name that starts with a role word and " - " is that role whatever follows
    ("Stab - Demo Pluck" is a stab): the remix build names an imported demo instrument that way when its own name says another role."""
    head = re.match(r"\s*([A-Za-z0-9]+)\s+-\s+", name)
    if head:
        lead = role_of(head.group(1))
        if lead:
            return lead
    tokens = [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]
    for role, words in ROLE_WORDS:
        if any(t == w or (len(w) >= 4 and t.startswith(w)) for t in tokens for w in words):
            return role
    return None


def tracks_in_use(f: flpfile.Flp) -> dict[int, list[int]]:
    """{mixer track: [channel ids]} for tracks with at least one enabled channel."""
    out: dict[int, list[int]] = {}
    for ch in f.channel_ids():
        info = f.channel_info(ch)
        if info["track"] is not None and info["enabled"] is not False:
            out.setdefault(info["track"], []).append(ch)
    return out


def track_role(f: flpfile.Flp, channels: list[int]) -> str | None:
    roles = [role_of(f.channel_info(c)["name"] or "") for c in channels]
    roles = [r for r in roles if r]
    return max(set(roles), key=roles.count) if roles else None


CONTROLLER_PLUGINS = ("Fruity Envelope Controller", "Fruity Keyboard Controller", "Fruity Formula Controller", "Fruity X-Y Controller", "MIDI Out")


def _kind(f: flpfile.Flp, ch: int) -> tuple:
    """(channel type byte, plugin internal name, Layer children) of channel ch."""
    a, b = f.block(ch)
    typ = next((bytes(v)[0] for e, v in f.events[a:b] if e == 21), None)
    plug = next((flpfile.dec16(v) for e, v in f.events[a:b] if e == 201), "")
    kids = [struct.unpack("<H", bytes(v))[0] for e, v in f.events[a:b] if e == 94 and len(v) == 2]
    return typ, plug, kids


def keep_on(f: flpfile.Flp, chans: list[int]) -> set[int]:
    """Channels a solo of `chans` must leave on: the part's channels, a Layer channel that triggers any of them (the notes are on the Layer),
    controller channels (an Envelope Controller pump, MIDI Out) and automation clips, so the part sounds as it does in the mix."""
    keep = set(chans)
    for ch in f.channel_ids():
        typ, plug, kids = _kind(f, ch)
        if (typ == 3 and keep & set(kids)) or typ == 5 or plug in CONTROLLER_PLUGINS:
            keep.add(ch)
    return keep


def solo_projects(f: flpfile.Flp, base: str, bypass_master: bool = False) -> dict[int, dict]:
    """Write nothing; return {track: {"role", "name", "channels", "flp": bytes}} where flp is the project with only that track's channels enabled
    (plus what keep_on keeps). bypass_master switches off the master's effect slots so a limiter does not shape every solo."""
    use = tracks_in_use(f)
    insert_names = {i["index"]: i["name"] for i in anatomy.inserts(f)}  # a part named only by its insert ("Vocal Chop", "FL Keys") still gets a role
    out = {}
    for track, chans in sorted(use.items()):
        if track == 0 and all(_kind(f, c)[0] in (3, 5) or _kind(f, c)[1] in CONTROLLER_PLUGINS for c in chans):
            continue  # only Layers, controllers and clips sit on the master: nothing to solo
        g = flpfile.Flp(f.head, [[e, v] for e, v in f.events], f.tail)
        keep = keep_on(f, chans)
        for ch in g.channel_ids():
            g.set_enabled(ch, ch in keep)
        if bypass_master:
            for slot in range(10):
                g.set_slot_enabled(0, slot, False)
        role = track_role(f, chans) or role_of(insert_names.get(track) or "")
        out[track] = {"role": role, "name": "%s__t%02d_%s" % (base, track, role or "mix"), "channels": chans, "flp": g.to_bytes()}
    return out


def part_level(path: str) -> dict:
    """Integrated loudness (LUFS), sample peak (dBFS) and active seconds of a solo render."""
    x, rate = dsp.load_audio(path)
    peak = float(abs(x).max())
    return {"lufs": round(dsp.integrated_loudness(x, rate), 2), "peak_db": round(dsp.db(peak), 2), "seconds": round(len(x) / rate, 1)}


def _role_levels(levels: dict[int, dict], roles: dict[int, str | None]) -> dict[str, float]:
    """Loudness of each role in LUFS: the energy sum of its tracks (parts are close to uncorrelated). Silent tracks are left out."""
    energy: dict[str, float] = {}
    for t, lv in levels.items():
        if roles.get(t) and lv["lufs"] > -70:
            energy[roles[t]] = energy.get(roles[t], 0.0) + 10 ** (lv["lufs"] / 10)
    return {r: dsp.power_db(e) for r, e in energy.items()}


def profile_from(levels: dict[int, dict], roles: dict[int, str | None], reference: str = "kick") -> dict:
    """Relative level of each role to the reference role, from measured solo levels {track: {"lufs": ..}}."""
    by_role = _role_levels(levels, roles)
    if reference not in by_role:
        raise ValueError("no %s track in the measured levels" % reference)
    return {"reference": reference, "relative_db": {r: round(v - by_role[reference], 1) for r, v in by_role.items()}}


def plan_changes(levels: dict[int, dict], roles: dict[int, str | None], faders_db: dict[int, float], profile: dict) -> list[dict]:
    """The fader change that moves each role to the profile's level relative to the reference role (the reference does not move). All tracks of a role get
    the same change. Changes under TOLERANCE_DB are skipped; the master (track 0) is never touched.
    new_db stops at the fader maximum and the change then reports clamped=True."""
    by_role = _role_levels(levels, roles)
    ref = profile["reference"]
    if ref not in by_role:
        raise ValueError("no %s track in the measured levels" % ref)
    out = []
    for role, now in sorted(by_role.items()):
        if role == ref or role not in profile["relative_db"]:
            continue
        delta = max(-MAX_STEP_DB, min(MAX_STEP_DB, by_role[ref] + profile["relative_db"][role] - now))
        if abs(delta) < TOLERANCE_DB:
            continue
        for t in sorted(t for t, r in roles.items() if r == role and t != 0 and t in faders_db and levels[t]["lufs"] > -70):
            want = faders_db[t] + delta
            out.append({"track": t, "role": role, "measured_lufs": levels[t]["lufs"], "role_delta_db": round(delta, 1), "new_db": round(min(want, FADER_MAX_DB), 1),
                        "clamped": want > FADER_MAX_DB})
    return out


def apply_changes(f: flpfile.Flp, changes: list[dict]) -> None:
    for c in changes:
        f.set_mixer_volume(c["track"], int(round(db_to_fader(c["new_db"]) * 16000)))


def faders_db(f: flpfile.Flp, tracks: list[int]) -> dict[int, float]:
    out = {}
    for t in tracks:
        raw = f.mixer_volume(t)
        if raw is not None:
            out[t] = round(fader_to_db(raw / 16000.0), 1)
    return out


def split_to_dir(project: str, out_dir: str, bypass_master: bool = False) -> dict:
    """Write one solo project per mixer track and manifest.json into out_dir; return the manifest {"project", "tracks": {track: {name, role, channels}}}."""
    f = flpfile.Flp.load(project)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    tracks = {}
    for t, s in solo_projects(f, safe_name(Path(project).stem), bypass_master).items():
        Path(out_dir, s["name"] + ".flp").write_bytes(s["flp"])
        tracks[str(t)] = {"name": s["name"], "role": s["role"], "channels": [f.channel_info(c)["name"] for c in s["channels"]]}
    man = {"project": project, "tracks": tracks}
    Path(out_dir, "manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    return man


def measure_dir(solo_dir: str, render_dir: str) -> tuple[dict, dict[int, dict], dict[int, str | None], list[str]]:
    """(manifest, levels, roles, tracks_without_a_render) for the solo projects in solo_dir and their renders in render_dir."""
    man = json.loads(Path(solo_dir, "manifest.json").read_text(encoding="utf-8"))
    levels, roles, missing = {}, {}, []
    for t, m in man["tracks"].items():
        wav = Path(render_dir, m["name"] + ".wav")
        if wav.is_file():
            levels[int(t)], roles[int(t)] = part_level(str(wav)), m["role"]
        else:
            missing.append(m["name"])
    return man, levels, roles, missing


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


def dump(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=True)
