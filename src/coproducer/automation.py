"""Automation clips in an FLP: build one, link it to a mixer parameter, put it in the playlist.

Format as FL 2026 (v26.1.7) saves it, read from projects FL wrote after "Create automation clip" on a mixer knob, a mixer EQ knob and a
plugin knob (2026-10-22; see docs/FLP_FORMAT.md, "Automation clips"). Three pieces make a working clip:

1. a channel block of type 5 (automation) whose event 234 holds the points,
2. one event 227 (20 bytes) before the first channel block that says which parameter the clip drives,
3. a playlist item that references the clip's channel id.

The mixer parameter id in the link is a 32-bit REC event id: 0x70000000 | track << 22 | sub << 16 | param.
Verified shapes: track volume 0x1FC0, pan 0x1FC1, stereo separation 0x1FC2 (sub 0); built-in EQ of a track is sub 9 (low freq 0x1FD8);
the first plugin slot's parameter k is 0x8000 + k (sub 0). Values in the points are the knob position from 0 to 1 (0.8 is 0 dB for a volume).
Positions are stored as beats since the previous point (the first is 0); this module takes and returns absolute beats (96 ticks per beat).
Measured 2026-10-22 by rendering ramps on a mixer track and the master: absolute positions written as stored deltas ran 2x to 3x slow.
"""
from __future__ import annotations

import itertools
import math
import struct

from .flpfile import EV_CH_ID, Flp, FlpError, enc16

TICKS_PER_BEAT = 96
MIXER_BASE = 0x70000000
P_VOLUME, P_PAN, P_STEREO_SEP = 0x1FC0, 0x1FC1, 0x1FC2
P_EQ_LOW_FREQ = 0x1FD8
PLUGIN_PARAM_BASE = 0x8000
EV_LINK = 227
EV_LINK_FORMULA = 230
EV_POINTS = 234
EV_CH_TYPE = 21
CH_TYPE_AUTOMATION = b"\x05"
POINT_SIZE = 24
# Events that FL 26.1.7 no longer writes but the old-format scratch base still carries. Injecting a clip into such a file made FL's
# command line render hang or crash (2026-10-22), so three or more of them mean "FL did not save this file". 67, 80, 94 and 192 were on this list
# until FL 26.1.7's own saves of the Future House demo and of our tech-house master showed FL writes them (2026-10-25).
LEGACY_EVENTS = (61, 62, 63, 66, 92, 93, 96, 120, 240)

# Events of one automation channel block as FL saved them, minus the id. "name" and "points" are filled in.
TEMPLATE: list[tuple] = [
    (21, "05"),
    (201, "0000"),
    (212, "0000000000000000ffffffff00000000540000000000000000000000000000000000000074000000c80000000000000000000000"),
    ("name", ""),
    (155, "00000000"),
    (128, "75895600"),
    (41, "01"),
    (0, "01"),
    (209, "0000000000190000000000000400000090000000"),
    (138, "80008000"),
    (139, "00000100"),
    (89, "0000"),
    (97, "8000"),
    (48, "00"),
    (69, "8000"),
    (86, "0001"),
    (71, "0004"),
    (83, "0000"),
    (74, "0000"),
    (75, "0000"),
    (76, "0000"),
    (85, "0008"),
    (131, "00008000"),
    (70, "0000"),
    (104, "0000"),
    (50, "01"),
    (219, "000000000032000000000000000100000000000000000000"),
    (229, "0000000000320000000000000000000000000000"),
    (221, "01000000f401000000"),
    (215, "ffffffff0000000001000000ffffffff3c0000000000803f0000803f0000803f0000803f0000803f0000000001000000ffffffff000400003000000000000100a7050000000000000001000000000000000000000000000000000000010000000000000000000000000000000000000002000000feffffffffffffff000000000000000000000000000000000000f03f0000000000000000ffffffff01010000000000000000e03f"),
    (132, "00000000"),
    (144, "00000000"),
    (145, "01000000"),
    ("points", ""),
    (32, "00"),
    (228, "64000000000000000000000000000000"),
    (228, "3c000000000000000000000000000000"),
    (218, "000000000000000064000000204e0000204e00003075000032000000204e00000000000064000000204e000000000000b680000000000000000000000000000000000000"),
    (218, "040000000000000064000000204e0000204e00003075000032000000204e00000000000064000000204e000000000000b68000000000000000000000000000009bffffff"),
    (218, "000000000000000064000000204e0000204e00003075000032000000204e00000000000064000000204e000000000000b680000000000000000000000000000000000000"),
    (218, "000000000000000064000000204e0000204e00003075000032000000204e00000000000064000000204e000000000000b680000000000000000000000000000000000000"),
    (218, "000000000000000064000000204e0000204e00003075000032000000204e00000000000064000000204e000000000000b680000000000000000000000000000000000000"),
    (143, "03000000"),
    (20, "00"),
    (170, "ffffffff"),
    (51, "00"),
]

# Bytes after the last point of event 234. Identical in every clip FL wrote (smoothing and LFO defaults).
POINTS_TAIL = bytes.fromhex("01000000ffffffffffffffffffffffffffffffff800000008000000000000000800000000500000003000000010000000000000000000000000000000000f03f00000000000000000100000000000000fffffffffffffffffffffffffbb2000000000000000000000000000000000000")

# The playlist item FL wrote for an automation clip (88 bytes); pos, channel, length, track and item id are replaced.
ITEM_TEMPLATE = bytes.fromhex("0000000000500d0090150000f20100007800400040648080000080bf000080bf0500000000000000000000000000000000000000000000000000000000000000000000000000f03f00000000ffffffff0000000000000000")


# Fader law of a mixer volume knob: (knob position, dB). Measured by rendering (2026-10-22); the 0.3 point came from the automation tests.
# Same table as modules/l2_verified/set_track_volume_db_verified plus that point. Good to about 0.5 dB; verify with a render when it matters.
FADER_LAW = ((0.0, -90.0), (0.25, -19.05), (0.3, -15.4), (0.5, -9.18), (0.8, 0.0), (1.0, 5.59))


def db_to_fader(db: float) -> float:
    """Knob position (0..1) of a mixer volume for a level in dB. -inf or very low gives 0.0. Above +5.59 dB it clamps to 1.0."""
    if db <= FADER_LAW[0][1]:
        return 0.0
    if db >= FADER_LAW[-1][1]:
        return 1.0
    for (v0, d0), (v1, d1) in itertools.pairwise(FADER_LAW):
        if db <= d1:
            if v0 == 0.0:  # below the lowest measured point the knob is close to linear in amplitude
                return max(0.0, 0.25 * 10 ** ((db - d1) / 20))
            return v0 + (v1 - v0) * (db - d0) / (d1 - d0)
    return 1.0


def fader_to_db(v: float) -> float:
    """Inverse of db_to_fader for 0.25 <= v <= 1.0 (the measured range); lower positions use the amplitude rule."""
    if v <= 0.0:
        return float("-inf")
    if v < 0.25:
        return -19.05 + 20 * math.log10(v / 0.25)
    for (v0, d0), (v1, d1) in itertools.pairwise(FADER_LAW[1:]):
        if v <= v1:
            return d0 + (d1 - d0) * (v - v0) / (v1 - v0)
    return FADER_LAW[-1][1]


def ramp_points(length: float, v_from: float, v_to: float) -> list[tuple]:
    """Straight line from v_from at beat 0 to v_to at `length` beats (a fade in, fade out or a filter or EQ sweep)."""
    if length <= 0:
        raise FlpError("ramp length must be positive")
    return [(0.0, v_from), (float(length), v_to)]


def duck_points(length: float, windows: list[tuple], normal: float, low: float, ramp: float = 0.125) -> list[tuple]:
    """Hold `normal`, dip to `low` inside each (start, end) window in beats from the clip start, with `ramp` beats to go down and come back.
    Used for ducking music under a vocal or a sidechain feel. Windows must be sorted, apart by more than 2 ramps and inside 0..length."""
    pts: list[tuple] = [(0.0, normal)]
    for a, b in windows:
        if b <= a or b > length or a < 0 or (a != 0 and a < ramp) or (len(pts) > 1 and a - ramp < pts[-1][0] + 1e-9):
            raise FlpError("bad duck window (%r, %r)" % (a, b))
        if a == 0:
            pts = [(0.0, low)]
        else:
            if a - ramp > pts[-1][0] + 1e-9:
                pts.append((a - ramp, normal))
            pts.append((a, low))
        if b + ramp < length:
            pts += [(b, low), (b + ramp, normal)]
        else:
            pts.append((b, low))
    if pts[-1][0] < length:
        pts.append((float(length), pts[-1][1]))
    return pts


def channels_with_sample(flp: Flp, marker: str) -> list[int]:
    """Channel ids whose sample path contains marker (case-insensitive), e.g. the folder of cleaned vocals."""
    out = []
    for ch in flp.channel_ids():
        a, b = flp.block(ch)
        path = next((bytes(v).decode("utf-16-le", "ignore") for e, v in flp.events[a:b] if e == 196), "")
        if marker.lower() in path.lower():
            out.append(ch)
    return out


def clip_windows(flp: Flp, channels: list[int], gap: float = 0.5) -> list[tuple]:
    """(start, end) in beats of the audio clips of these channels in the playlist, merged when the gap between them is at most `gap` beats."""
    want, spans = set(channels), []
    for it in flp.playlist_items():
        if struct.unpack("<H", it[6:8])[0] in want:
            a = struct.unpack("<I", it[0:4])[0] / TICKS_PER_BEAT
            spans.append((a, a + struct.unpack("<I", it[8:12])[0] / TICKS_PER_BEAT))
    out: list[list] = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def mixer_link(track: int, param: int = P_VOLUME, *, sub: int = 0) -> int:
    """REC event id of a mixer parameter. track 0 is the master. For a plugin knob pass param=PLUGIN_PARAM_BASE + index."""
    if not 0 <= track < 128:
        raise FlpError("mixer track %d out of range" % track)
    return MIXER_BASE | (track << 22) | (sub << 16) | param


def decode_link(value: int) -> dict:
    return {"track": (value - MIXER_BASE) >> 22, "sub": (value >> 16) & 0x3F, "param": value & 0xFFFF}


def encode_link(clip_channel: int, link: int) -> bytes:
    """The 20-byte event 227: u16 0, u16 clip channel id, u32 0, u32 link, u32 8, u32 469 (the last two were the same in every clip)."""
    return struct.pack("<HHIIII", 0, clip_channel, 0, link, 8, 469)


def encode_points(points: list[tuple], *, bipolar: bool = False) -> bytes:
    """Event 234 body. points are (beat, value[, tension]) sorted by beat; value is the knob position 0..1.
    bipolar is the flag FL sets on centred knobs (pan, stereo separation)."""
    if len(points) < 2:
        raise FlpError("an automation clip needs at least two points")
    beats = [p[0] for p in points]
    if beats != sorted(beats):
        raise FlpError("points must be sorted by position")
    out = struct.pack("<IIIBII", 1, 64, 0x401 if bipolar else 0x400, 0, 3, len(points))
    if beats[0] != 0:
        raise FlpError("the first point must be at beat 0 (start the clip where you want the first value)")
    for i, p in enumerate(points):
        if not 0.0 <= p[1] <= 1.0:
            raise FlpError("point value %r outside 0..1" % (p[1],))
        tension = p[2] if len(p) > 2 else 0.0
        delta = 0.0 if i == 0 else p[0] - points[i - 1][0]
        out += struct.pack("<ddfBBBB", delta, p[1], tension, 0, 0, 0, 0 if i == 0 else 2)
    return out + POINTS_TAIL


def decode_points(data: bytes) -> list[tuple]:
    """(absolute beat, value, tension) per point."""
    n = struct.unpack_from("<I", data, 17)[0]
    out, t = [], 0.0
    for i in range(n):
        d, v, tn = struct.unpack_from("<ddf", data, 21 + i * POINT_SIZE)
        t += d
        out.append((t, v, tn))
    return out


def legacy_events(flp: Flp) -> list[int]:
    """The legacy event ids present in the project (see LEGACY_EVENTS)."""
    have = {e for e, _ in flp.events}
    return [e for e in LEGACY_EVENTS if e in have]


def first_free_track(flp: Flp) -> int:
    """Lowest 1-based playlist track that holds no item."""
    used = {499 - struct.unpack("<H", it[12:14])[0] for it in flp.playlist_items()}
    return next(t for t in range(1, 500) if t not in used)


def next_channel_id(flp: Flp) -> int:
    return max(flp.channel_ids() + [0]) + 1


_TARGETS = {"track_volume": (P_VOLUME, 0, False), "track_pan": (P_PAN, 0, True), "track_stereo_sep": (P_STEREO_SEP, 0, True),
            "eq_gain": (0x1FD0, 9, False), "eq_freq": (0x1FD8, 9, False), "eq_q": (0x1FE0, 9, False)}


CHANNEL_PARAMS = {"volume": (0, False), "pan": (1, True), "filter_cutoff": (2, False), "filter_resonance": (3, False), "pitch": (4, True)}


def channel_link(channel: int, param: int) -> int:
    """Link id of a channel parameter: channel << 16 | param (REC channel codes; 0x8000 + k is the channel's generator parameter k). Read from
    FL's own saves: a snare's pitch clip is 0x100004 (channel 16, code 4) and a Harmless knob 0x188034 (channel 24, parameter 52)."""
    if not 0 <= channel < 0x1000:
        raise FlpError("channel %d out of range" % channel)
    return channel << 16 | param


def resolve_target(target: dict) -> tuple[int, bool]:
    """(link, bipolar) for {'kind': track_volume | track_pan | track_stereo_sep | eq_gain | eq_freq | eq_q | plugin_param, 'track': n,
    'band': 0..2 (eq kinds), 'param': index and 'slot': 0..9 (plugin_param)}, or {'kind': channel_param, 'channel': id, 'param': volume | pan |
    filter_cutoff | filter_resonance | pitch} or {'kind': generator_param, 'channel': id, 'param': index}. track 0 is the master."""
    kind, track = target.get("kind"), int(target.get("track", -1))
    if kind == "channel_param":
        if target.get("param") not in CHANNEL_PARAMS:
            raise FlpError("channel parameter must be one of %s" % sorted(CHANNEL_PARAMS))
        code, bipolar = CHANNEL_PARAMS[target["param"]]
        return channel_link(int(target.get("channel", -1)), code), bipolar
    if kind == "generator_param":
        idx = int(target.get("param", -1))
        if not 0 <= idx < 0x2000:
            raise FlpError("generator parameter index %d out of range" % idx)
        return channel_link(int(target.get("channel", -1)), PLUGIN_PARAM_BASE + idx), False
    if kind == "plugin_param":
        slot, idx = int(target.get("slot", 0)), int(target.get("param", -1))
        if not 0 <= slot <= 9:
            raise FlpError("effect slot %d out of range" % slot)  # slot k is sub k: read from FL's own saves (the Future House demo, 2026-10-25)
        if not 0 <= idx < 0x2000:
            raise FlpError("plugin parameter index %d out of range" % idx)
        return mixer_link(track, PLUGIN_PARAM_BASE + idx, sub=slot), False
    if kind not in _TARGETS:
        raise FlpError("unknown automation target %r" % (kind,))
    base, sub, bipolar = _TARGETS[kind]
    band = int(target.get("band", 0)) if sub == 9 else 0
    if not 0 <= band <= 2:
        raise FlpError("eq band must be 0, 1 or 2")
    return mixer_link(track, base + band, sub=sub), bipolar


def curve_points(curve: dict, unit: str = "knob") -> list[tuple]:
    """Points from {'points': [{'beat','value'}...]} or {'ramp': {'length','from','to'}} or {'duck': {'length','windows','normal','low','ramp'}}.
    unit 'db' converts values from dB with the volume fader law."""
    conv = db_to_fader if unit == "db" else float
    if len(curve) != 1:
        raise FlpError("curve needs exactly one of points, ramp or duck")
    if "points" in curve:
        return [(float(p["beat"]), conv(p["value"])) for p in curve["points"]]
    if "ramp" in curve:
        r = curve["ramp"]
        return ramp_points(r["length"], conv(r["from"]), conv(r["to"]))
    if "duck" in curve:
        d = curve["duck"]
        return duck_points(d["length"], [tuple(w) for w in d["windows"]], conv(d["normal"]), conv(d["low"]), d.get("ramp", 0.125))
    raise FlpError("curve needs points, ramp or duck")


def add_automation_clip(flp: Flp, channel_id: int, name: str, link: int, points: list[tuple], *, start_beat: float = 0.0,
                        track: int = 1, bipolar: bool = False, color: bytes | None = None, allow_legacy: bool = False) -> int:
    """Add the clip to the project. Returns the playlist item count. channel_id must be unused; track is the 1-based playlist track.
    The clip is as long as its last point."""
    if channel_id in flp.channel_ids():
        raise FlpError("channel id %d already exists" % channel_id)
    old = legacy_events(flp)
    if len(old) >= 3 and not allow_legacy:
        raise FlpError("this project was not saved by FL Studio (legacy events %s); open and save it in FL first, then patch the saved copy" % old)
    block = []
    for eid, hx in TEMPLATE:
        if eid == "name":
            block.append([203, enc16(name)])
        elif eid == "points":
            block.append([EV_POINTS, encode_points(points, bipolar=bipolar)])
        else:
            data = bytes.fromhex(hx)
            if eid == 128 and color is not None:
                data = color
            block.append([eid, data])
    block.insert(0, [EV_CH_ID, struct.pack("<H", channel_id)])
    last = flp.channel_ids()[-1]
    _, end = flp.block(last)
    flp.events[end:end] = block
    flp._set_channel_count(flp.channel_count + 1)
    _place_links(flp, encode_link(channel_id, link))
    # playlist item
    items = flp.playlist_items()
    nid = max([struct.unpack("<I", it[32:36])[0] for it in items] + [0]) + 1
    it = bytearray(ITEM_TEMPLATE)
    it[0:4] = struct.pack("<I", round(start_beat * TICKS_PER_BEAT))
    it[6:8] = struct.pack("<H", channel_id)
    it[8:12] = struct.pack("<I", round((points[-1][0]) * TICKS_PER_BEAT))
    it[12:14] = struct.pack("<H", 499 - track)
    it[32:36] = struct.pack("<I", nid)
    items.append(bytes(it))
    items.sort(key=lambda x: struct.unpack("<I", x[0:4])[0])
    flp.events[flp._playlist_index()][1] = b"".join(items)
    return len(items)


def place_clip_copies(flp: Flp, channel_id: int, start_beats: list[float], track: int) -> int:
    """Put more playlist items of an existing automation clip (the same clip played again, as the reference repeats a one-beat wobble 64 times).
    Returns the playlist item count."""
    items = flp.playlist_items()
    mine = [it for it in items if struct.unpack("<H", it[6:8])[0] == channel_id]
    if not mine:
        raise FlpError("automation clip %d is not on the playlist" % channel_id)
    nid = max(struct.unpack("<I", it[32:36])[0] for it in items) + 1
    for k, beat in enumerate(start_beats):
        it = bytearray(mine[0])
        it[0:4] = struct.pack("<I", round(beat * TICKS_PER_BEAT))
        it[12:14] = struct.pack("<H", 499 - track)
        it[32:36] = struct.pack("<I", nid + k)
        items.append(bytes(it))
    items.sort(key=lambda x: struct.unpack("<I", x[0:4])[0])
    flp.events[flp._playlist_index()][1] = b"".join(items)
    return len(items)


def _place_links(flp: Flp, new_link: bytes) -> None:
    """FL writes every controller event (226 MIDI, then 227 remote links) together, just before the first channel block. A link can be
    followed by its formula text (event 230); the pair is one unit and must stay together (a DTP project with two such pairs hung FL's
    render when the pairs were split, 2026-10-22). Older files keep 226 events between channel blocks, so gather them all, keep their
    order, append the new link, and put the group in FL's place."""
    keep: list[list] = []
    links: list[list] = []
    rest: list[list] = []
    ev = flp.events
    i = 0
    while i < len(ev):
        e, v = ev[i]
        if e == 226:
            keep.append([e, bytes(v)])
        elif e == EV_LINK:
            links.append([e, bytes(v)])
            if i + 1 < len(ev) and ev[i + 1][0] == EV_LINK_FORMULA:
                links.append([EV_LINK_FORMULA, bytes(ev[i + 1][1])])
                i += 1
        else:
            rest.append(ev[i])
        i += 1
    flp.events[:] = rest
    at = flp._starts()[0]
    flp.events[at:at] = keep + links + [[EV_LINK, new_link]]


def remove_automation_clip(flp: Flp, channel_id: int) -> None:
    """Delete a clip: its channel block, its link event and its playlist items in every arrangement."""
    a, b = flp.block(channel_id)
    del flp.events[a:b]
    out, drop_formula = [], False
    for x in flp.events:
        if x[0] == EV_LINK and len(x[1]) == 20 and struct.unpack_from("<H", bytes(x[1]), 2)[0] == channel_id:
            drop_formula = True
            continue
        if x[0] == EV_LINK_FORMULA and drop_formula:
            continue
        drop_formula = False
        out.append(x)
    flp.events[:] = out
    flp._map_all_playlists(lambda items: [it for it in items if struct.unpack("<H", it[6:8])[0] != channel_id])
    flp._set_channel_count(flp.channel_count - 1)


def list_automation(flp: Flp) -> list[dict]:
    """Every automation clip in the project: channel id, name, link, points."""
    links = {}
    for e, v in flp.events:
        if e == EV_LINK and len(v) == 20:
            _, ch, _, lk, _, _ = struct.unpack("<HHIIII", v)
            links[ch] = lk
    out = []
    for ch in flp.channel_ids():
        a, b = flp.block(ch)
        evs = flp.events[a:b]
        if any(e == EV_CH_TYPE and bytes(v) == CH_TYPE_AUTOMATION for e, v in evs):
            pts = next((bytes(v) for e, v in evs if e == EV_POINTS), b"")
            name = next((v for e, v in evs if e == 203), b"")
            out.append({"channel": ch, "name": name.decode("utf-16-le").rstrip("\x00"), "link": links.get(ch), "points": decode_points(pts) if pts else []})
    return out
