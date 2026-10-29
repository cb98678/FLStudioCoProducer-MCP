"""Names, colours and groups inside an FL Studio project file: channels, channel groups, mixer inserts, patterns and playlist tracks.

Event ids are from PyFLP (https://github.com/demberto/PyFLP, pyflp/channel.py and mixer.py) and were checked against FL 26.1.7 files:
channel colour 128 (RGB plus one zero byte), channel group index 145 (int32), group names 231, pattern colour 150, insert colour 149, insert name 204,
playlist track record 238 (index u32, colour 4 bytes) with an optional name 239 after it. An insert block starts at a routing event 235; the Nth block
is mixer insert N+1 (master is not a block). That mapping was read off the stem project (stems on inserts 6 to 9 are the blocks 5 to 8) and the v13_2 project
(the insert named "Chop hook #2" is the block of insert 12). Colours are (r, g, b).
"""
from __future__ import annotations

import struct

from .flpfile import EV_CH_ID, EV_PATNAME, EV_NEWPAT, Flp, FlpError, dec16, enc16

EV_CH_COLOR, EV_CH_GROUP, EV_GROUP_NAME = 128, 145, 231
EV_PAT_COLOR, EV_INS_COLOR, EV_INS_NAME, EV_INS_ROUTING, EV_INS_OUTPUT, EV_INS_ICON = 150, 149, 204, 235, 147, 95
EV_TRACK_DATA, EV_TRACK_NAME, EV_TRACK_EXTRA = 238, 239, 43
EV_CH_NAME = 203
EV_INS_FLAGS = 42
EV_CH_FLAG = 41
DEFAULT_CH_COLOR = (92, 101, 106)
Rgb = tuple[int, int, int]


def rgb_bytes(rgb: Rgb) -> bytes:
    return bytes((*rgb, 0))


def rgb_of(raw: bytes) -> Rgb:
    return (raw[0], raw[1], raw[2])


# ---- channels
def channel_color(f: Flp, ch: int) -> Rgb:
    return rgb_of(f.events[f._find(ch, EV_CH_COLOR)][1])


def set_channel_color(f: Flp, ch: int, rgb: Rgb) -> None:
    """Colour a channel. FL shows the colour only when the channel's appearance flag (event 41) is 1; with 0 it falls back to grey (seen in a file FL saved)."""
    f.events[f._find(ch, EV_CH_COLOR)][1] = rgb_bytes(rgb)
    f.events[f._find(ch, EV_CH_FLAG)][1] = b"\x01"


def set_channel_name(f: Flp, ch: int, name: str) -> None:
    f.set_text(ch, EV_CH_NAME, name)


def display_groups(f: Flp) -> list[str]:
    """Names of the channel rack groups in file order; a channel's group number is an index into this list."""
    return [dec16(v) for e, v in f.events if e == EV_GROUP_NAME]


def set_display_groups(f: Flp, wanted: list[str]) -> dict[str, int]:
    """Make sure every name in `wanted` is a channel rack group and return {name: index}. FL sorts group names alphabetically when it loads a file but keeps the
    stored indices, so a list in any other order shows every channel in the wrong group (seen: Kick landed in FX). The names are therefore written sorted, and
    the group index of every channel is remapped by name."""
    old = display_groups(f)
    final = sorted(set(old) | set(wanted), key=str.lower)
    at = [i for i, (e, _v) in enumerate(f.events) if e == EV_GROUP_NAME]
    first = at[0] if at else min(i for i, (e, _v) in enumerate(f.events) if e == EV_CH_ID)
    for i in reversed(at):
        del f.events[i]
    f.events[first:first] = [[EV_GROUP_NAME, enc16(n)] for n in final]
    for ch in f.channel_ids():
        try:
            k = f._find(ch, EV_CH_GROUP)
        except FlpError:
            continue
        was = struct.unpack("<i", f.events[k][1])[0]
        if 0 <= was < len(old):
            f.events[k][1] = struct.pack("<i", final.index(old[was]))
    return {n: final.index(n) for n in wanted}


def shown_group(f: Flp, ch: int) -> str | None:
    """The group FL shows a channel in: the stored index read against the alphabetically sorted names."""
    names = sorted(display_groups(f), key=str.lower)
    i = channel_group(f, ch)
    return names[i] if 0 <= i < len(names) else None


def shown_channel_color(f: Flp, ch: int) -> Rgb:
    """The colour FL shows for a channel: the stored colour when the appearance flag is 1, else the default grey."""
    return channel_color(f, ch) if f.events[f._find(ch, EV_CH_FLAG)][1] == b"\x01" else DEFAULT_CH_COLOR


def channel_group(f: Flp, ch: int) -> int:
    return struct.unpack("<i", f.events[f._find(ch, EV_CH_GROUP)][1])[0]


def set_channel_group(f: Flp, ch: int, index: int) -> None:
    f.events[f._find(ch, EV_CH_GROUP)][1] = struct.pack("<i", index)


# ---- mixer inserts
def _insert_starts(f: Flp) -> list[int]:
    return [i for i, (e, _v) in enumerate(f.events) if e == EV_INS_ROUTING]


def insert_range(f: Flp, track: int) -> tuple[int, int]:
    """Event range of the block of mixer insert `track` (1 and up)."""
    starts = _insert_starts(f)
    if not 1 <= track <= len(starts):
        raise FlpError("mixer insert %d has no block in this file (blocks: %d)" % (track, len(starts)))
    end = starts[track] if track < len(starts) else min(i for i, (e, _v) in enumerate(f.events) if e == 47 and i > starts[track - 1])
    return starts[track - 1], end


def insert_name(f: Flp, track: int) -> str:
    i, j = insert_range(f, track)
    return next((dec16(v) for e, v in f.events[i:j] if e == EV_INS_NAME), "")


def shown_insert_color(f: Flp, track: int) -> Rgb | None:
    """The colour FL shows for a mixer insert: the stored colour when the appearance flag (event 42) is 1, else none."""
    i, j = insert_range(f, track)
    on = any(e == EV_INS_FLAGS and v == b"\x01" for e, v in f.events[i:j])
    return insert_color(f, track) if on else None


def insert_color(f: Flp, track: int) -> Rgb | None:
    i, j = insert_range(f, track)
    return next((rgb_of(v) for e, v in f.events[i:j] if e == EV_INS_COLOR), None)


def set_insert(f: Flp, track: int, name: str | None = None, rgb: Rgb | None = None) -> None:
    """Name and/or colour mixer insert `track`. Events are placed where FL writes them: colour after the output event, name after the icon."""
    for what, eid, value, after in (("color", EV_INS_COLOR, rgb_bytes(rgb) if rgb else None, (EV_INS_OUTPUT,)),
                                    ("name", EV_INS_NAME, enc16(name) if name is not None else None, (EV_INS_ICON, EV_INS_FLAGS))):
        if value is None:
            continue
        i, j = insert_range(f, track)
        hit = [k for k in range(i, j) if f.events[k][0] == eid]
        if hit:
            f.events[hit[0]][1] = value
            continue
        anchor = max([k for k in range(i, j) if f.events[k][0] in after] or [i])
        f.events.insert(anchor + 1, [eid, value])
    if rgb:  # FL honours an insert colour only when the appearance flag (event 42) is 1; every coloured block FL writes has it
        i, j = insert_range(f, track)
        flag = [k for k in range(i, j) if f.events[k][0] == EV_INS_FLAGS]
        if flag:
            f.events[flag[0]][1] = b"\x01"
        else:
            anchor = max([k for k in range(i, j) if f.events[k][0] in (EV_INS_OUTPUT, EV_INS_COLOR)] or [i])
            f.events.insert(anchor + 1, [EV_INS_FLAGS, b"\x01"])


# ---- patterns
def _pattern_at(f: Flp, pid: int) -> int:
    for i, (e, v) in enumerate(f.events):
        if e == EV_NEWPAT and len(v) == 2 and int.from_bytes(v, "little") == pid and i + 1 < len(f.events) and f.events[i + 1][0] == EV_PATNAME:
            return i
    raise FlpError("pattern %d not in file" % pid)


def pattern_name(f: Flp, pid: int) -> str:
    return dec16(f.events[_pattern_at(f, pid) + 1][1])


def set_pattern_color(f: Flp, pid: int, rgb: Rgb) -> None:
    i = _pattern_at(f, pid)
    if f.events[i + 2][0] == EV_PAT_COLOR:
        f.events[i + 2][1] = rgb_bytes(rgb)
    else:
        f.events.insert(i + 2, [EV_PAT_COLOR, rgb_bytes(rgb)])


# ---- playlist tracks (1 is the top row)
def _track_at(f: Flp, index: int) -> int:
    """Track record of the current arrangement (each arrangement has its own 500 rows)."""
    a, b = f.arrangement_range()
    for i in range(a, b):
        e, v = f.events[i]
        if e == EV_TRACK_DATA and struct.unpack("<I", v[:4])[0] == index:
            return i
    raise FlpError("playlist track %d not in the current arrangement" % index)


def track_name(f: Flp, index: int) -> str:
    i = _track_at(f, index)
    j = i + 1
    while j < len(f.events) and f.events[j][0] == EV_TRACK_EXTRA:
        j += 1
    return dec16(f.events[j][1]) if j < len(f.events) and f.events[j][0] == EV_TRACK_NAME else ""


def set_playlist_track(f: Flp, index: int, name: str | None = None, rgb: Rgb | None = None) -> None:
    i = _track_at(f, index)
    if rgb:
        f.events[i][1] = f.events[i][1][:4] + rgb_bytes(rgb) + f.events[i][1][8:]
        if f.events[i + 1][0] == EV_TRACK_EXTRA:  # the flag event after the record: 1 makes FL keep the colour (confirmed in an FL-saved file)
            f.events[i + 1][1] = b"\x01"
        else:
            f.events.insert(i + 1, [EV_TRACK_EXTRA, b"\x01"])
    if name is not None:
        j = i + 1
        while j < len(f.events) and f.events[j][0] == EV_TRACK_EXTRA:
            j += 1
        if j < len(f.events) and f.events[j][0] == EV_TRACK_NAME:
            f.events[j][1] = enc16(name)
        else:
            f.events.insert(j, [EV_TRACK_NAME, enc16(name)])


DEFAULT_ROW_COLOR = (72, 81, 86)


def shown_row_color(f: Flp, index: int) -> Rgb:
    """The colour FL shows for a playlist row: the stored colour when the flag event after the record is 1, else the default."""
    i = _track_at(f, index)
    on = f.events[i + 1][0] == EV_TRACK_EXTRA and f.events[i + 1][1] == b"\x01"
    return rgb_of(f.events[i][1][4:8]) if on else DEFAULT_ROW_COLOR
