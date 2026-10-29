"""The house standard for how a project looks: names, colours and channel groups, the same in every project.

FL Studio has no official colour standard. The nearest published habit (https://www.audeobox.com/learn/fl-studio/fl-studio-channel-rack-template-setup-guide/)
is red for drums, blue for melodic parts, green for effect sends and yellow for buses. This project uses the person's own scheme, chosen 2026-10-24:
drums green, bass orange, synths purple, vocals blue, FX red, buses yellow. One family is one colour in the channel rack, the mixer, the pattern list
and the playlist rows, so a part is the same colour wherever it shows up. Families come from names (partmix.role_of); a part with no known family is
left alone and reported. Nothing here moves a fader, changes routing or touches a plugin.

Automation clips are not a family: whatever their name says, they go into an Automation group with one blue-grey colour, and their clips sit in a
block of rows right below the music, one row per clip channel in the order they first play, each row named after its clip (the person approved
this block, copied from the Future House reference, 2026-10-25; the colour is a pick, not theirs). Audio clips with no family go into an Audio group.
"""
from __future__ import annotations

import re
import struct

from . import flporg, partmix
from .flpfile import PATTERN_BASE, Flp, FlpError

PALETTE = {"drums": (76, 175, 80), "bass": (255, 152, 20), "synths": (156, 39, 176), "vocals": (33, 150, 243), "fx": (244, 67, 54), "bus": (255, 235, 59)}
FAMILY = {"drums": "drums", "kick": "drums", "clap": "drums", "hats": "drums", "perc": "drums", "reese": "bass", "sub": "bass", "bass": "bass", "stab": "synths",
          "arp": "synths", "chops": "vocals", "vocal": "vocals", "fx": "fx", "orig": "synths"}
GROUP = {"drums": "Drums", "bass": "Bass", "synths": "Synths", "vocals": "Vocals", "fx": "FX"}
ROLE_LABEL = {"drums": "Drums", "kick": "Kick", "clap": "Snare Clap", "hats": "Hats", "perc": "Perc", "reese": "Reese Bass", "sub": "Sub Bass", "bass": "Bass", "stab": "Stab",
              "arp": "Arp", "chops": "Chops", "vocal": "Vocal", "fx": "FX", "orig": "Original"}
AUTOMATION_COLOR = (120, 144, 156)
AUTOMATION_TYPE, AUDIO_TYPE = 5, 4
UPPER = {"fx": "FX", "bpm": "BPM", "ch": "CH", "oh": "OH", "dj": "DJ"}


def tidy(name: str) -> str:
    """A channel name in house style: no CP_ prefix, no underscores or hashes, Title Case, closed and open hats called Hat Closed and Hat Open."""
    s = re.sub(r"^cp[_ -]", "", name.strip(), flags=re.I).replace("_", " ").replace("#", " ")
    tokens = [t for t in s.split() if t]
    low = [t.lower() for t in tokens]
    if partmix.role_of(name) == "hats":
        if "ch" in low or "closed" in low:
            return "Hat Closed"
        if "oh" in low or "open" in low:
            return "Hat Open"
    return " ".join(UPPER.get(t.lower(), t.capitalize()) for t in tokens)


def role_of(name: str) -> str | None:
    """partmix.role_of plus the group words a playlist uses (Drums), which are not a mixer role."""
    if name.strip().lower() in ("drum", "drums") or name.lower().startswith(("drums ", "drum ")):
        return "drums"
    return partmix.role_of(name)


def family_of(name: str) -> str | None:
    role = role_of(name)
    return FAMILY.get(role) if role else None


def _unique(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else "%s %d" % (n, seen[n]))
    return out


def plan_channels(f: Flp) -> list[dict]:
    """Per channel: id, old and new name, family, colour and group. Names are made unique by a trailing number."""
    ids = f.channel_ids()
    old = [f.channel_info(c)["name"] or "" for c in ids]
    new = _unique([tidy(n) for n in old])
    rows = []
    for c, o, n in zip(ids, old, new):
        kind = f.channel_type(c)
        if kind == AUTOMATION_TYPE:
            rows.append({"channel": c, "old": o, "new": n, "family": "automation", "color": AUTOMATION_COLOR, "group": "Automation"})
            continue
        fam = family_of(o)
        group = GROUP.get(fam) if fam else ("Audio" if kind == AUDIO_TYPE else None)
        rows.append({"channel": c, "old": o, "new": n, "family": fam, "color": PALETTE[fam] if fam else None, "group": group})
    return rows


def _automation_ids(f: Flp) -> set[int]:
    return {c for c in f.channel_ids() if f.channel_type(c) == AUTOMATION_TYPE}


def plan_automation_rows(f: Flp) -> list[dict]:
    """The automation block: per automation clip channel with clips, the rows (0-based) its clips are on now, the row it belongs on (right below
    the last row that holds anything else, in the order the clips first play) and that row's name and colour. index is the row counted from 1."""
    auto = _automation_ids(f)
    first: dict[int, int] = {}
    now: dict[int, set] = {}
    music = []
    for it in f.playlist_items():
        ref, pos, row = struct.unpack("<H", it[6:8])[0], struct.unpack("<I", it[0:4])[0], 499 - struct.unpack("<H", it[12:14])[0]
        if ref in auto:
            first[ref] = min(first.get(ref, pos), pos)
            now.setdefault(ref, set()).add(row)
        else:
            music.append(row)
    start = max(music, default=-1) + 1
    order = sorted(first, key=lambda c: (first[c], c))
    names = _unique([tidy(f.channel_info(c)["name"] or "Automation") for c in order])
    return [{"channel": c, "name": n, "rows": sorted(now[c]), "row": start + k, "index": start + k + 1, "color": AUTOMATION_COLOR}
            for k, (c, n) in enumerate(zip(order, names))]


def _move_clips(f: Flp, channel: int, row: int) -> None:
    f.map_playlist(lambda it: it[:12] + struct.pack("<H", 499 - row) + it[14:] if struct.unpack("<H", it[6:8])[0] == channel else it)


def plan_tracks(f: Flp) -> list[dict]:
    """Per used mixer track: its new name (the channel's own when it has one channel, else the role label), family and colour."""
    chans = {r["channel"]: r for r in plan_channels(f)}
    rows, names = [], []
    for track, ids in sorted(partmix.tracks_in_use(f).items()):
        if track == 0:
            continue
        role = partmix.track_role(f, ids)
        fam = FAMILY.get(role) if role else None
        try:
            old = flporg.insert_name(f, track)
        except FlpError:
            continue  # no insert block in this file for that track
        names.append(chans[ids[0]]["new"] if len(ids) == 1 else ROLE_LABEL.get(role or "", "Track %d" % track))
        rows.append({"track": track, "old": old, "family": fam, "color": PALETTE[fam] if fam else None, "channels": ids})
    for r, n in zip(rows, _unique(names)):
        r["new"] = n
    return rows


def _pattern_family(name: str) -> str | None:
    return family_of(name.split(" ")[0]) if name else None


def plan_patterns(f: Flp) -> list[dict]:
    return [{"pattern": p, "name": flporg.pattern_name(f, p), "family": fam, "color": PALETTE[fam]}
            for p in f.pattern_ids() if (fam := _pattern_family(flporg.pattern_name(f, p)))]


def plan_rows(f: Flp) -> list[dict]:
    """Per playlist row that holds clips: the family of what it holds, the row name and colour. Row 1 is the top. Mixed rows are left alone."""
    names = {c: f.channel_info(c)["name"] or "" for c in f.channel_ids()}
    pat = {p: flporg.pattern_name(f, p) for p in f.pattern_ids()}
    held: dict[int, list[str]] = {}
    auto = _automation_ids(f)
    for it in f.playlist_items():
        ref = struct.unpack("<H", it[6:8])[0]
        if ref in auto:
            continue  # the automation block has its own rows (plan_automation_rows)
        label = pat.get(ref - PATTERN_BASE, "") if ref > PATTERN_BASE else names.get(ref, "")
        held.setdefault(499 - struct.unpack("<H", it[12:14])[0] + 1, []).append(label)
    rows = []
    for index, labels in sorted(held.items()):
        roles = {role_of(l.split(" ")[0] if l in pat.values() else l) for l in labels}
        fams = {FAMILY.get(r) if r else None for r in roles}
        if len(fams) == 1 and None not in fams:
            fam = fams.pop()
            name = ROLE_LABEL[roles.pop()] if len(roles) == 1 else fam.capitalize()
            try:
                old = flporg.track_name(f, index)
            except FlpError:
                continue  # that playlist row has no track record in this file
            rows.append({"index": index, "old": old, "new": name, "family": fam, "color": PALETTE[fam]})
    for r, n in zip(rows, _unique([r["new"] for r in rows])):
        r["new"] = n
    return rows


def unused_channels(f: Flp) -> list[dict]:
    """Enabled channels that play nothing: no note in any pattern and no clip in the playlist. Automation-only or MIDI-driven channels would also show here, so
    this lists candidates; removal is a separate choice (drop_unused). A channel a Layer plays is in use: the Layer holds its notes."""
    clipped = {struct.unpack("<H", it[6:8])[0] for it in f.playlist_items()}
    layered = {k for c in f.channel_ids() for k in f.layer_children(c)}
    return [{"channel": c, "name": f.channel_info(c)["name"] or "", "track": f.channel_info(c)["track"]}
            for c in f.channel_ids() if f.channel_info(c)["enabled"] is not False and not f.note_ticks(c) and c not in clipped and c not in layered]


def drop_unused(f: Flp) -> list[dict]:
    """Remove the strays: channels that play nothing and are not routed to any mixer insert (track 0 or none). A silent channel that sits on an insert may be a
    kit voice kept for later, so it stays and shows up in unused_channels only. The ids are made contiguous again. Returns what was removed."""
    gone = [u for u in unused_channels(f) if not u["track"]]
    for u in gone:
        f.remove_channel(u["channel"])
    if gone:
        f.renumber_channels()
    return gone


def plan(f: Flp) -> dict:
    return {"channels": plan_channels(f), "tracks": plan_tracks(f), "patterns": plan_patterns(f), "rows": plan_rows(f), "automation_rows": plan_automation_rows(f)}


def _try(fn, *args, **kw) -> bool:
    """Run one setter; False when the project has no such event (a synthetic or stripped project). Real FL projects always have them."""
    try:
        fn(*args, **kw)
        return True
    except FlpError:
        return False


def apply(f: Flp, p: dict) -> dict:
    """Write a plan into the project. Returns counts of what changed and `skipped`, the things the file has no event for. Channel groups are added when missing."""
    skipped = 0
    group_index = flporg.set_display_groups(f, sorted({r["group"] for r in p["channels"] if r["group"]}))
    for r in p["channels"]:
        if r["new"] != r["old"]:
            skipped += not _try(flporg.set_channel_name, f, r["channel"], r["new"])
        if r["color"]:
            skipped += not _try(flporg.set_channel_color, f, r["channel"], r["color"])
        if r["group"]:
            skipped += not _try(flporg.set_channel_group, f, r["channel"], group_index[r["group"]])
    for r in p["tracks"]:
        skipped += not _try(flporg.set_insert, f, r["track"], name=r["new"], rgb=r["color"])
    for r in p["patterns"]:
        skipped += not _try(flporg.set_pattern_color, f, r["pattern"], r["color"])
    for r in p["rows"]:
        skipped += not _try(flporg.set_playlist_track, f, r["index"], name=r["new"], rgb=r["color"])
    for r in p.get("automation_rows", []):
        _move_clips(f, r["channel"], r["row"])
        skipped += not _try(flporg.set_playlist_track, f, r["index"], name=r["name"], rgb=r["color"])
    return {**{k: len(v) for k, v in p.items()}, "skipped": skipped}


def _color_is(getter, f: Flp, key: int, want) -> bool:
    try:
        return getter(f, key) == want
    except FlpError:
        return True  # nothing to compare in a file without that event


def check(f: Flp) -> list[str]:
    """Problems against the standard, one sentence each; empty when the project already looks the standard way."""
    out = []
    p = plan(f)
    out += ["channel %d: name %r should be %r" % (r["channel"], r["old"], r["new"]) for r in p["channels"] if r["new"] != r["old"]]
    out += ["channel %d (%s): colour should be %s" % (r["channel"], r["new"], r["color"]) for r in p["channels"]
            if r["color"] and not _color_is(flporg.shown_channel_color, f, r["channel"], r["color"])]
    out += ["channel %d (%s): group should be %s" % (r["channel"], r["new"], r["group"]) for r in p["channels"]
            if r["group"] and not _color_is(flporg.shown_group, f, r["channel"], r["group"])]
    out += ["mixer track %d: name %r should be %r" % (r["track"], r["old"], r["new"]) for r in p["tracks"] if r["new"] != r["old"]]
    out += ["mixer track %d: colour should be %s" % (r["track"], r["color"]) for r in p["tracks"]
            if r["color"] and not _color_is(flporg.shown_insert_color, f, r["track"], r["color"])]
    out += ["playlist row %d: name %r should be %r" % (r["index"], r["old"], r["new"]) for r in p["rows"] if r["new"] != r["old"]]
    out += ["playlist row %d: colour should be %s" % (r["index"], r["color"]) for r in p["rows"]
            if not _color_is(flporg.shown_row_color, f, r["index"], r["color"])]
    out += ["automation clip %d (%s): on playlist row %s, should be on row %d in the automation block below the music"
            % (r["channel"], r["name"], ", ".join(str(x + 1) for x in r["rows"]), r["index"]) for r in p["automation_rows"] if r["rows"] != [r["row"]]]
    out += ["playlist row %d: name should be %r (automation block)" % (r["index"], r["name"]) for r in p["automation_rows"]
            if not _name_is(f, r["index"], r["name"])]
    return out


def _name_is(f: Flp, index: int, want: str) -> bool:
    try:
        return flporg.track_name(f, index) == want
    except FlpError:
        return True
