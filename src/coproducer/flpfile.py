"""FL Studio 2026 .flp reader and patcher: the offline route to editable parts.

The FL API cannot write a pattern's notes or add playlist clips, so editable-first remixes are built by patching
a sandbox copy of the project file. Layout facts are in docs/FLP_FORMAT.md. Every edit keeps the file round-trip
exact for untouched events (parse then emit gives the same bytes). Never run this on the user's original.
"""
from __future__ import annotations

import math
import os
import re
import struct
from pathlib import Path

EV_CH_ENABLED = 0
EV_CH_TRACK = 104
EV_CH_ID = 64
EV_NEWPAT = 65
EV_ARRANGEMENT = 99
EV_ARR_NAME = 241
EV_ARR_CURRENT = 100
EV_MARKER_POS = 148
EV_MARKER_NAME = 205
EV_PATNAME = 193
EV_SAMPLE_PATH = 196
EV_CH_NAME = 203
EV_PATNOTES = 224
EV_PLUGIN_STATE = 213
EV_PLAYLIST = 233
EV_MIXER = 225
EV_LOOP_ACTIVE = 9
EV_LAYER_CHILD = 94  # one per channel a Layer channel plays (u16 channel id)
EV_LEVELS = 219  # channel levels: i32 pan, volume, pitch knob in cents, filter mod x, mod y, filter type
EV_CH_PARAMS = 215
EV_LINK = 227  # a controller or automation link: u16, u16 source channel, u32, u32 target, u32, u32
CHANNEL_FILTERS = {"fast_lp": 0, "lp": 1, "bp": 2, "hp": 3, "bs": 4, "lpx2": 5, "svf_lp": 6, "svf_lpx2": 7}
PITCH_RANGE_AT = 112  # i32 in event 215: the pitch knob's range in semitones (2 by default), read from FL 26 saves of the Future House demo
MIXER_VOLUME = 8128
NOTE_SIZE = 24
PLAYLIST_ITEM_SIZE = 88
# Playlist item size by the FL version that saved the file, read from the 20 FL demo projects (2026-10-27): FL 12 and 20.8 write 32 bytes,
# 20.99 to 24.1 write 60, 24.2 to 25 write 80, FL 26 writes 88. The fields this reader uses (position 0, reference 6, length 8, track 12,
# audio start and end 24 and 28) sit at the same offsets in all four.
PLAYLIST_ITEM_SIZES = ((26, 0, 88), (24, 2, 80), (20, 99, 60), (0, 0, 32))
PATTERN_BASE = 20480
# Playlist item flags (u16 at byte 18 of every item size): 0x40 on every clip FL saves; 0x2000 marks a clip muted in the playlist. Not in
# PyFLP's struct (it documents the word as "Always (64, 0)"); found 2026-10-28 from the FL demo songs: all seven solo renders whose clips all
# carried 0x2000 came out digitally silent, and every solo with one clip without it had sound.
ITEM_FLAGS_AT = 18
ITEM_MUTED = 0x2000
# A one-bar pattern clip as FL 26.1.7 writes it (taken from a real project, id and position zeroed): the layout used when a project has no pattern clip yet.
PATTERN_CLIP_TEMPLATE = bytes.fromhex(
    "0000000000501e5080010000c80100007800400040648080ffffffffffffffff06000000000000000000000000000000000000000000803f"
    "0000000000000000000000000000f03f00000000ffffffff0000000000000000")
EV_TEMPO = 156
EV_DATA_FOLDER = 202  # the project's data folder (text); FL writes extracted stems to its Audio subfolder
EV_TRACK = 238  # a playlist row: u32 index, u32 colour, u32 icon, u8 enabled at 12, ..., u8 grouped at 46
EV_TRACK_NAME = 239  # a playlist row's name, right after its record
TICKS_PER_BEAT = 96
TICKS_PER_BAR = 384
MAX_PATTERN_ID = 5000


class FlpError(ValueError):
    """Raised for a structural problem; the message says which assumption failed."""


def varlen(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def enc16(s: str) -> bytes:
    return (s + "\x00").encode("utf-16-le")


def dec16(b: bytes) -> str:
    return b.decode("utf-16-le", errors="ignore").rstrip("\x00")


def _events(data: bytes, p: int, end: int) -> list[list]:
    """Read the event stream data[p:end]. Each event is [id, value bytes]."""
    events: list[list] = []
    while p < end:
        e = data[p]
        p += 1
        if e == 172 and data[p + 3 : p + 4] == b"\xc0":
            n = 3  # FL 26.1.7 writes this event with 3 bytes, the 4th is the id of the project title text event that follows
        elif e == 172 and data[p + 4 : p + 6] == b"\x00\xed":
            n = 5  # its second occurrence (after the data folder text): 5 bytes, then event 237 (two doubles). Read as 4 bytes the stream falls out of step
        elif e < 64:
            n = 1
        elif e < 128:
            n = 2
        elif e < 192:
            n = 4
        else:
            n = 0
            shift = 0
            while True:
                b = data[p]
                p += 1
                n |= (b & 0x7F) << shift
                shift += 7
                if not b & 0x80:
                    break
        if p + n > end:
            raise FlpError("event %d runs past the end of its stream" % e)
        events.append([e, bytes(data[p : p + n])])
        p += n
    return events


def parse(data: bytes) -> tuple[bytes, list[list], bytes]:
    """Split a file into (head, events, tail). Each event is [id, value bytes]."""
    if data[:4] != b"FLhd":
        raise FlpError("not an FLP file (no FLhd)")
    hl = struct.unpack("<I", data[4:8])[0]
    head = data[: 8 + hl]
    p = 8 + hl
    if data[p : p + 4] != b"FLdt":
        raise FlpError("no FLdt chunk after the header")
    end = p + 8 + struct.unpack("<I", data[p + 4 : p + 8])[0]
    p += 8
    events = _events(data, p, end)
    return head, events, data[end:]


def emit(head: bytes, events: list[list], tail: bytes) -> bytes:
    body = bytearray()
    for e, v in events:
        body.append(e)
        if e >= 192:
            body += varlen(len(v))
        body += v
    return head + b"FLdt" + struct.pack("<I", len(body)) + bytes(body) + tail


def note_bytes(pos: int, channel: int, key: int, length: int = 0, vel: int = 100, pan: int = 64) -> bytes:
    """One 24-byte pattern note. pos is in ticks from the pattern start (96 per beat, 384 per 4/4 bar). length 0 suits one-shots."""
    return struct.pack("<IHHIHH", pos, 0x4000, channel, length, key, 0) + bytes(
        [0x78, 0, 0x40, 0, max(0, min(128, pan)), max(1, min(127, vel)), 0x80, 0x80]
    )


class Flp:
    """An FLP held as head, an event list and a tail, with helpers for the edits a remix needs."""

    def __init__(self, head: bytes, events: list[list], tail: bytes) -> None:
        self.head, self.events, self.tail = head, events, tail

    @classmethod
    def load(cls, path: str | Path) -> "Flp":
        return cls(*parse(Path(path).read_bytes()))

    def to_bytes(self) -> bytes:
        return emit(self.head, self.events, self.tail)

    def save(self, path: str | Path) -> None:
        """Write and re-parse; refuse to leave a file that does not round-trip, or one whose timing or layout these helpers do not know.
        The file is written next to its destination and moved into place, so an interrupted save never leaves half a project."""
        self.check_editable()
        data = self.to_bytes()
        if emit(*parse(data)) != data:
            raise FlpError("re-parse of the patched file does not round-trip")
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)  # callers check the sandbox first; a new run folder may not exist yet (2026-10-25)
        tmp = dest.with_name(dest.name + ".part")
        tmp.write_bytes(data)
        os.replace(tmp, dest)

    @property
    def ppq(self) -> int:
        """Ticks per beat from the header. Every tick constant here (TICKS_PER_BEAT, TICKS_PER_BAR) assumes 96."""
        return struct.unpack("<H", self.head[12:14])[0] if len(self.head) >= 14 else TICKS_PER_BEAT

    def fl_version(self) -> str | None:
        """The FL version that saved the file (event 199), or None."""
        for e, v in self.events:
            if e == 199:
                raw = bytes(v)
                return (raw.decode("utf-16-le", "replace") if len(raw) > 1 and raw[1] == 0 else raw.decode("ascii", "replace")).rstrip("\x00")
        return None

    def playlist_item_size(self, length: int | None = None) -> int:
        """Bytes per playlist item for this file's FL version (PLAYLIST_ITEM_SIZES); when a playlist's length does not divide by it, the
        largest known size that does (a file saved by a version between the measured ones)."""
        ver = self.fl_version() or ""
        parts = [int(x) for x in ver.split(".")[:2] if x.isdigit()] + [0, 0]
        size = next(sz for major, minor, sz in PLAYLIST_ITEM_SIZES if (parts[0], parts[1]) >= (major, minor)) if ver else PLAYLIST_ITEM_SIZE
        if length is None or length % size == 0:
            return size
        return next((sz for _a, _b, sz in PLAYLIST_ITEM_SIZES if length % sz == 0), size)

    def _items(self, v: bytes) -> list[bytes]:
        n = self.playlist_item_size(len(v))
        return [v[k : k + n] for k in range(0, len(v) - n + 1, n)]

    def check_editable(self) -> None:
        """Refuse files the patchers would damage: a PPQ other than 96 (every position would land in the wrong place) or a save older than FL 21
        (event layouts differ). The fix in both cases is in FL: set PPQ 96 in the project settings, or re-save in FL 26."""
        if self.ppq != TICKS_PER_BEAT:
            raise FlpError("the project uses PPQ %d; these edits assume 96. Set PPQ to 96 in FL (Options > Project general settings) and save" % self.ppq)
        ver = self.fl_version()
        major = ver.split(".")[0] if ver else ""
        if major.isdigit() and int(major) < 21:
            raise FlpError("the project was saved by FL %s; re-save it in FL 26 before editing" % ver)

    # ---- channels
    @property
    def channel_count(self) -> int:
        return struct.unpack("<H", self.head[10:12])[0]

    def _set_channel_count(self, n: int) -> None:
        self.head = self.head[:10] + struct.pack("<H", n) + self.head[12:]

    def _starts(self) -> list[int]:
        """Event indexes where a channel block starts. A 64 event directly before a pattern id (65) is the pattern region's
        current-item marker in FL 2026, not a channel."""
        ev = self.events
        return [i for i, (e, v) in enumerate(ev) if e == EV_CH_ID and not (i + 1 < len(ev) and ev[i + 1][0] == EV_NEWPAT)]

    def channel_ids(self) -> list[int]:
        return [int.from_bytes(self.events[i][1], "little") for i in self._starts()]

    def block(self, ch: int) -> tuple[int, int]:
        """Event index range [start, end) of channel ch: from its id event to the next id event or the arrangement event."""
        starts = self._starts()
        ids = [int.from_bytes(self.events[i][1], "little") for i in starts]
        if ch not in ids:
            raise FlpError("channel %d not in file" % ch)
        i = starts[ids.index(ch)]
        for j in range(i + 1, len(self.events)):
            if j in starts or self.events[j][0] == EV_ARRANGEMENT:
                return i, j
        return i, len(self.events)

    def plugin_preset_name(self, ch: int) -> str | None:
        """Name of the preset loaded in a Serum 2 channel, read from the plain JSON header of the plugin state (event 213), or None."""
        i, j = self.block(ch)
        for k in range(i, j):
            if self.events[k][0] == EV_PLUGIN_STATE:
                m = re.search(rb'"presetName":"([^"]*)"', self.events[k][1])
                if m:
                    return m.group(1).decode("utf-8", errors="replace")
        return None

    def plugin_state(self, ch: int) -> bytes | None:
        """The plugin event data (213) of a channel, or None for a channel without a plugin state."""
        i, j = self.block(ch)
        return next((bytes(self.events[k][1]) for k in range(i, j) if self.events[k][0] == EV_PLUGIN_STATE), None)

    def set_plugin_state(self, ch: int, data: bytes) -> None:
        """Replace a channel's plugin event data (a Serum 2 state from serumstate, for example). The plugin itself stays the same."""
        self.events[self._find(ch, EV_PLUGIN_STATE)][1] = bytes(data)

    def _find(self, ch: int, eid: int) -> int:
        i, j = self.block(ch)
        for k in range(i, j):
            if self.events[k][0] == eid:
                return k
        raise FlpError("channel %d has no event %d" % (ch, eid))

    def get_text(self, ch: int, eid: int) -> str:
        return dec16(self.events[self._find(ch, eid)][1])

    def data_folder(self) -> str | None:
        """The project's data folder (FL saves "Extract stems from sample" results in its Audio subfolder, 2026-10-29)."""
        v = next((v for e, v in self.events if e == EV_DATA_FOLDER), None)
        return dec16(bytes(v)) if v is not None else None

    def set_data_folder(self, path: str) -> None:
        """Point the project's data folder somewhere else (a folder path as FL on the host will see it, ending in a backslash)."""
        i = next((k for k, (e, _) in enumerate(self.events) if e == EV_DATA_FOLDER), None)
        if i is None:
            raise FlpError("this project has no data folder event to change")
        self.events[i][1] = enc16(path if path.endswith(("\\", "/")) else path + "\\")

    def set_text(self, ch: int, eid: int, text: str) -> None:
        self.events[self._find(ch, eid)][1] = enc16(text)

    def set_sample(self, ch: int, path: str, name: str | None = None) -> None:
        """Point a sampler channel at a wav (an absolute path as FL on the host will see it) and optionally rename it."""
        self.set_text(ch, EV_SAMPLE_PATH, path)
        if name:
            self.set_text(ch, EV_CH_NAME, name)

    def set_enabled(self, ch: int, on: bool) -> None:
        i, j = self.block(ch)
        for k in range(i, j):
            if self.events[k][0] == EV_CH_ENABLED and len(self.events[k][1]) == 1:
                self.events[k][1] = bytes([1 if on else 0])
                return
        raise FlpError("channel %d has no enabled flag" % ch)

    def set_track(self, ch: int, track: int) -> None:
        self.events[self._find(ch, EV_CH_TRACK)][1] = struct.pack("<H", track)

    def clone_channel(self, src: int, new_id: int, name: str, track: int | None = None) -> None:
        """Copy channel src (plugin state included) as a new channel with its own name and optional mixer track."""
        self.import_channel(self, src, new_id, name, track)

    def import_channel(self, source: "Flp", src: int, new_id: int, name: str, track: int | None = None) -> None:
        """Copy channel src of another project (or this one) in as a new channel; plugin state travels with the block."""
        if new_id in self.channel_ids():
            raise FlpError("channel id %d already exists" % new_id)
        i, j = source.block(src)
        copy = [[e, bytes(v)] for e, v in source.events[i:j]]
        copy[0][1] = struct.pack("<H", new_id)
        for x in copy:
            if x[0] == EV_CH_NAME:
                x[1] = enc16(name)
            if x[0] == EV_CH_TRACK and track is not None:
                x[1] = struct.pack("<H", track)
        last = self.channel_ids()[-1]
        _, end = self.block(last)
        self.events[end:end] = copy
        self._set_channel_count(self.channel_count + 1)

    def remove_channel(self, ch: int) -> None:
        """Delete channel ch (its whole block). Notes on it stay in patterns until strip_notes; its playlist clips stay until clear_playlist."""
        i, j = self.block(ch)
        del self.events[i:j]
        self._set_channel_count(self.channel_count - 1)

    def renumber_channels(self) -> dict[int, int]:
        """Make channel ids contiguous from 0 (FL treats an id as a rack slot, so gaps show as blank sampler channels). Updates the id events, every note's
        channel field, the channel reference of audio clips in the playlist of every arrangement, the channels Layer channels play, and the source and
        channel target of controller and automation links (event 227). Returns {old_id: new_id}."""
        ids = self.channel_ids()
        mapping = {old: new for new, old in enumerate(ids)}
        for i in self._starts():
            self.events[i][1] = struct.pack("<H", mapping[int.from_bytes(self.events[i][1], "little")])
        self._remap_links(mapping)
        for i in self._note_events():
            v = bytearray(self.events[i][1])
            for k in range(0, len(v) - NOTE_SIZE + 1, NOTE_SIZE):
                old = struct.unpack("<H", v[k + 6 : k + 8])[0]
                if old in mapping:
                    v[k + 6 : k + 8] = struct.pack("<H", mapping[old])
            self.events[i][1] = bytes(v)
        def remap(items: list[bytes]) -> list[bytes]:
            out = []
            for it in items:
                ref = struct.unpack("<H", it[6:8])[0]
                if ref < PATTERN_BASE and ref in mapping:
                    it = it[:6] + struct.pack("<H", mapping[ref]) + it[8:]
                out.append(it)
            return out

        self._map_all_playlists(remap)
        return mapping

    # ---- mixer
    def _mixer_index(self) -> int:
        for i, (e, v) in enumerate(self.events):
            if e == EV_MIXER:
                return i
        raise FlpError("no mixer state event")

    def set_mixer_volume(self, track: int, fader: int) -> None:
        """Set an insert's fader (12800 is 0 dB) in the existing mixer state record. Only tracks that already have a volume record can be set."""
        i = self._mixer_index()
        v = bytearray(self.events[i][1])
        key = 0x7000 + 64 * track
        for k in range(0, len(v) - 11, 12):
            _a, param, who, _val = struct.unpack("<IHHI", v[k : k + 12])
            if param == MIXER_VOLUME and who == key:
                v[k + 8 : k + 12] = struct.pack("<I", fader)
                self.events[i][1] = bytes(v)
                return
        raise FlpError("mixer track %d has no volume record" % track)

    def set_slot_enabled(self, track: int, slot: int, on: bool) -> bool:
        """Switch one effect slot of a mixer track on or off (its record in event 225). Returns False when the file has no record for it."""
        i = self._mixer_index()
        v = bytearray(self.events[i][1])
        key = 0x7000 + 64 * track + slot
        for k in range(0, len(v) - 11, 12):
            _a, param, who, _val = struct.unpack("<IHHI", v[k : k + 12])
            if param & 0xFF == 0 and who == key:
                v[k + 8 : k + 12] = struct.pack("<I", 1 if on else 0)
                self.events[i][1] = bytes(v)
                return True
        return False

    def remove_slot_plugin(self, track: int, slot: int) -> str | None:
        """Empty one effect slot of a mixer insert: drop the plugin's events (201 name, 212 wrapper, 155, 128, 213 state) and keep the slot's
        own event 98, which is all an empty slot holds in FL saves. For a render copy without a plugin this FL edition lacks (its trial dialog
        stalls a command-line render). Returns the plugin's name, or None when the slot was already empty."""
        ev = self.events
        marks = [i for i, (e, _v) in enumerate(ev) if e == 236]
        if track >= len(marks):
            raise FlpError("no mixer insert %d" % track)
        end = marks[track + 1] if track + 1 < len(marks) else len(ev)
        i = marks[track] + 1
        while i < end:
            if ev[i][0] == 201:
                j = i + 1
                while j < end and ev[j][0] != 98:
                    j += 1
                wrap = next((bytes(ev[k][1]) for k in range(i, j) if ev[k][0] == 212), b"")
                if len(wrap) >= 8 and struct.unpack_from("<I", wrap, 4)[0] == slot:
                    name = dec16(bytes(ev[i][1])).rstrip("\x00")
                    del ev[i:j]
                    return name
                i = j
            i += 1
        return None

    def mixer_volume(self, track: int) -> int | None:
        v = self.events[self._mixer_index()][1]
        key = 0x7000 + 64 * track
        for k in range(0, len(v) - 11, 12):
            _a, param, who, val = struct.unpack("<IHHI", v[k : k + 12])
            if param == MIXER_VOLUME and who == key:
                return val
        return None


    def _remap_links(self, mapping: dict[int, int]) -> None:
        for x in self.events:
            v = bytes(x[1])
            if x[0] == EV_LAYER_CHILD and len(v) == 2 and struct.unpack("<H", v)[0] in mapping:
                x[1] = struct.pack("<H", mapping[struct.unpack("<H", v)[0]])
            elif x[0] == EV_LINK and len(v) >= 12:
                out, src, mid, target = struct.unpack_from("<HHII", v)
                if target < 0x70000000 and (target >> 16) in mapping:  # a channel target (channel << 16 | code); 0x70000000 and up is the mixer
                    target = mapping[target >> 16] << 16 | (target & 0xFFFF)
                if src < 0x8000:  # sources 0x8000 and up are not channels (the reference has 0x8900 for a mixer meter link)
                    src = mapping.get(src, src)
                x[1] = struct.pack("<HHII", out, src, mid, target) + v[12:]

    # ---- channel pitch and Layer channels
    def channel_pitch(self, ch: int) -> tuple[int, int]:
        """(pitch knob in cents, knob range in semitones) of channel ch. FL clamps the knob to its range, and a pitch automation clip spans it."""
        lv = bytes(self.events[self._find(ch, EV_LEVELS)][1])
        pr = bytes(self.events[self._find(ch, EV_CH_PARAMS)][1])
        rng = struct.unpack_from("<i", pr, PITCH_RANGE_AT)[0] if len(pr) >= PITCH_RANGE_AT + 4 else 2
        return struct.unpack_from("<i", lv, 8)[0], rng

    def set_pitch_range(self, ch: int, semitones: int) -> None:
        if not 1 <= semitones <= 48:
            raise FlpError("pitch range %d out of 1..48 semitones" % semitones)
        k = self._find(ch, EV_CH_PARAMS)
        v = bytearray(self.events[k][1])
        if len(v) < PITCH_RANGE_AT + 4:
            raise FlpError("channel %d has a short parameter event (not an FL 26 save)" % ch)
        v[PITCH_RANGE_AT : PITCH_RANGE_AT + 4] = struct.pack("<i", semitones)
        self.events[k][1] = bytes(v)

    def set_channel_pitch(self, ch: int, cents: int) -> None:
        """Set the pitch knob in cents (-4800..4800), widening the knob's range when it is too small to hold the value."""
        if abs(cents) > 4800:
            raise FlpError("pitch %d cents out of range" % cents)
        k = self._find(ch, EV_LEVELS)
        v = bytearray(self.events[k][1])
        v[8:12] = struct.pack("<i", int(cents))
        self.events[k][1] = bytes(v)
        need = -(-abs(int(cents)) // 100)
        if need > self.channel_pitch(ch)[1]:
            self.set_pitch_range(ch, need)

    def set_channel_pan(self, ch: int, pan: float) -> None:
        """Channel pan knob, -1 (left) to 1 (right); 0 is the centre (6400 in the levels event)."""
        k = self._find(ch, EV_LEVELS)
        v = bytearray(self.events[k][1])
        v[0:4] = struct.pack("<i", int(round(6400 + 6400 * max(-1.0, min(1.0, pan)))))
        self.events[k][1] = bytes(v)

    def set_channel_volume_raw(self, ch: int, raw: int) -> None:
        """Channel volume knob, 0..12800 (10000 is FL's default, 78%)."""
        k = self._find(ch, EV_LEVELS)
        v = bytearray(self.events[k][1])
        v[4:8] = struct.pack("<i", max(0, min(12800, int(raw))))
        self.events[k][1] = bytes(v)

    def channel_type(self, ch: int) -> int | None:
        """Event 21 of channel ch: 0 sampler, 2 plugin, 3 Layer, 4 audio clip, 5 automation clip (None when the block has none)."""
        i, j = self.block(ch)
        return next((bytes(v)[0] for e, v in self.events[i:j] if e == 21 and len(v) >= 1), None)

    def set_channel_filter(self, ch: int, kind: str, cutoff: int, resonance: int = 0) -> None:
        """The channel filter in the levels event: type (FL's order Fast LP, LP, BP, HP, BS, LPx2, SVF LP, SVF LPx2), cutoff (mod x) and resonance
        (mod y), each 0..256. The reference high-passes its top kick at cutoff 193 and low-passes its body kick at 76."""
        if kind not in CHANNEL_FILTERS:
            raise FlpError("unknown filter %r (known: %s)" % (kind, ", ".join(CHANNEL_FILTERS)))
        k = self._find(ch, EV_LEVELS)
        v = bytearray(self.events[k][1])
        v[12:24] = struct.pack("<3i", max(0, min(256, int(cutoff))), max(0, min(256, int(resonance))), CHANNEL_FILTERS[kind])
        self.events[k][1] = bytes(v)

    def layer_children(self, ch: int) -> list[int]:
        i, j = self.block(ch)
        return [struct.unpack("<H", bytes(v))[0] for e, v in self.events[i:j] if e == EV_LAYER_CHILD and len(v) == 2]

    def set_layer_children(self, ch: int, children: list[int]) -> None:
        """Replace the channels a Layer channel plays. FL writes the 94 events right after the mixer track event (104)."""
        i, j = self.block(ch)
        keep = [x for x in self.events[i:j] if x[0] != EV_LAYER_CHILD]
        at = next((k + 1 for k, x in enumerate(keep) if x[0] == EV_CH_TRACK), len(keep))
        keep[at:at] = [[EV_LAYER_CHILD, struct.pack("<H", c)] for c in children]
        self.events[i:j] = keep

    def move_notes(self, src: int, dst: int) -> int:
        """Give every pattern note of channel src to channel dst. Returns how many notes moved."""
        moved = 0
        for i in self._note_events():
            v = bytearray(self.events[i][1])
            for k in range(0, len(v) - NOTE_SIZE + 1, NOTE_SIZE):
                if struct.unpack("<H", v[k + 6 : k + 8])[0] == src:
                    v[k + 6 : k + 8] = struct.pack("<H", dst)
                    moved += 1
            self.events[i][1] = bytes(v)
        return moved

    # ---- inspection (read only)
    def channel_info(self, ch: int) -> dict:
        """Name, sample path, mixer track, enabled flag and Serum preset name of channel ch (None where the channel has none)."""
        i, j = self.block(ch)
        d: dict = {"name": None, "sample": None, "track": None, "enabled": None, "preset": self.plugin_preset_name(ch)}
        for e, v in self.events[i:j]:
            if e == EV_CH_NAME:
                d["name"] = dec16(v)
            elif e == EV_SAMPLE_PATH:
                d["sample"] = dec16(v)
            elif e == EV_CH_TRACK and len(v) == 2:
                d["track"] = struct.unpack("<H", v)[0]
            elif e == EV_CH_ENABLED and len(v) == 1 and d["enabled"] is None:
                d["enabled"] = bool(v[0])
        return d

    def pattern_notes(self) -> dict[int, list[tuple]]:
        """{pattern_id: [(pos_ticks, channel, key, length_ticks, velocity)]} for every pattern that has notes."""
        out: dict[int, list[tuple]] = {}
        cur = None
        for e, v in self.events:
            if e == EV_NEWPAT:
                cur = int.from_bytes(v, "little")
            elif e == EV_PATNOTES and cur is not None:
                for k in range(0, len(v) - NOTE_SIZE + 1, NOTE_SIZE):
                    pos, _fl, ch, ln, key, _x = struct.unpack_from("<IHHIHH", v, k)
                    out.setdefault(cur, []).append((pos, ch, key, ln, v[k + 21]))
        return out

    @staticmethod
    def item_muted(it: bytes) -> bool:
        """True for a playlist clip muted in the playlist (it does not play or render)."""
        return len(it) >= ITEM_FLAGS_AT + 2 and bool(struct.unpack_from("<H", it, ITEM_FLAGS_AT)[0] & ITEM_MUTED)

    def pattern_clips(self, muted: bool = False) -> list[tuple[int, int, int]]:
        """Playlist pattern clips as (pattern_id, pos_ticks, length_ticks): the clips that play (muted=True adds the muted ones)."""
        out = []
        for it in self.playlist_items():
            ref = struct.unpack("<H", it[6:8])[0]
            if ref > PATTERN_BASE and (muted or not self.item_muted(it)):
                out.append((ref - PATTERN_BASE, struct.unpack("<I", it[0:4])[0], struct.unpack("<I", it[8:12])[0]))
        return out

    def audio_clips(self, muted: bool = False) -> list[dict]:
        """Playlist audio clips as dicts: channel, pos and length in ticks, and the content window start_ms and end_ms; the clips that play
        (muted=True adds the muted ones)."""
        out = []
        for it in self.playlist_items():
            ref = struct.unpack("<H", it[6:8])[0]
            if ref <= PATTERN_BASE and (muted or not self.item_muted(it)):
                s_ms, e_ms = struct.unpack("<ff", it[24:32])
                out.append({"channel": ref, "pos": struct.unpack("<I", it[0:4])[0], "length": struct.unpack("<I", it[8:12])[0], "start_ms": s_ms, "end_ms": e_ms})
        return out

    def note_ticks(self, ch: int) -> list[int]:
        """Absolute start of every note of channel ch on the playlist, in ticks: each pattern clip's position plus the note position.
        Notes past the end of a clip are ignored (the clip plays only its own length); a clip longer than its pattern is not looped here."""
        notes = self.pattern_notes()
        ticks = []
        for pid, pos, length in self.pattern_clips():
            for npos, nch, _key, _ln, _vel in notes.get(pid, []):
                if nch == ch and npos < length:
                    ticks.append(pos + npos)
        return sorted(ticks)

    # ---- patterns
    # ---- arrangements (FL 20.7+ keeps several; FL plays and renders the current one, event 100)
    def arrangements(self) -> list[dict]:
        """Every arrangement: id, name, event range [start, end) and the index of its playlist event (None when it has none)."""
        ev = self.events
        starts = [i for i, (e, _v) in enumerate(ev) if e == EV_ARRANGEMENT]
        stop = next((i for i, (e, _v) in enumerate(ev) if e == EV_ARR_CURRENT), len(ev))
        out = []
        for k, a in enumerate(starts):
            b = starts[k + 1] if k + 1 < len(starts) else max(stop, a + 1)
            if b <= a:
                b = len(ev)
            row = {"id": int.from_bytes(ev[a][1], "little"), "name": None, "start": a, "end": b, "playlist": None}
            for i in range(a, b):
                if ev[i][0] == EV_ARR_NAME and row["name"] is None:
                    row["name"] = dec16(ev[i][1])
                elif ev[i][0] == EV_PLAYLIST and row["playlist"] is None:
                    row["playlist"] = i
            out.append(row)
        return out

    def current_arrangement(self) -> dict | None:
        """The arrangement FL plays: the one event 100 names, else the first."""
        arrs = self.arrangements()
        if not arrs:
            return None
        cur = next((int.from_bytes(v, "little") for e, v in self.events if e == EV_ARR_CURRENT), None)
        return next((a for a in arrs if a["id"] == cur), arrs[0])

    def arrangement_range(self) -> tuple[int, int]:
        """Event range of the current arrangement, or the whole file when there is no arrangement event."""
        a = self.current_arrangement()
        return (a["start"], a["end"]) if a else (0, len(self.events))

    def time_markers(self) -> list[dict]:
        """Time markers of the current arrangement: position in ticks and name."""
        a, b = self.arrangement_range()
        out = []
        for i in range(a, b):
            e, v = self.events[i]
            if e == EV_MARKER_POS and len(v) == 4:
                out.append({"pos": struct.unpack("<I", v)[0] & 0x07FFFFFF, "name": None})
            elif e == EV_MARKER_NAME and out and out[-1]["name"] is None:
                out[-1]["name"] = dec16(v)
        return out

    def add_time_marker(self, pos_ticks: int, name: str) -> None:
        """Add a time marker to the current arrangement, as FL 26 writes one: events 148 (position), 33 and 34 (4/4), 46, 45, 168, 101, then 205
        (name), kept in position order right after the arrangement's playlist event."""
        a = self.current_arrangement()
        if not a or a["playlist"] is None:
            raise FlpError("no arrangement playlist to put a marker after")
        group = [[EV_MARKER_POS, struct.pack("<I", pos_ticks)], [33, b"\x04"], [34, b"\x04"], [46, b"\x00"], [45, b"\x00"], [168, bytes(4)],
                 [101, bytes(2)], [EV_MARKER_NAME, enc16(name)]]
        at = a["playlist"] + 1
        while at < a["end"] and self.events[at][0] == EV_MARKER_POS and struct.unpack("<I", bytes(self.events[at][1]))[0] & 0x07FFFFFF <= pos_ticks:
            at += 1
            while at < a["end"] and self.events[at][0] not in (EV_MARKER_POS, 238):
                at += 1
        self.events[at:at] = group

    def _playlist_index(self) -> int:
        """Playlist event of the current arrangement (older files without arrangement events: the first playlist event)."""
        a = self.current_arrangement()
        if a and a["playlist"] is not None:
            return a["playlist"]
        if not a:
            for i, (e, v) in enumerate(self.events):
                if e == EV_PLAYLIST:
                    return i
        raise FlpError("no playlist event in the current arrangement")

    def _playlist_indexes(self) -> list[int]:
        return [i for i, (e, _v) in enumerate(self.events) if e == EV_PLAYLIST]

    def _map_all_playlists(self, fn) -> None:
        """Apply fn(list of items) -> list of items to the playlist of every arrangement (channel ids are global)."""
        for i in self._playlist_indexes():
            v = self.events[i][1]
            items = self._items(v)
            self.events[i][1] = b"".join(fn(items))

    def _patterns_end(self) -> int:
        """Patterns sit before the first arrangement."""
        for i, (e, _v) in enumerate(self.events):
            if e in (EV_ARRANGEMENT, EV_PLAYLIST):
                return i
        raise FlpError("no arrangement or playlist event")

    def pattern_ids(self) -> list[int]:
        pl = self._patterns_end()
        return [int.from_bytes(v, "little") for e, v in self.events[:pl] if e == EV_NEWPAT and int.from_bytes(v, "little") < MAX_PATTERN_ID]

    def next_pattern_id(self, floor: int = 1) -> int:
        return max([floor - 1] + self.pattern_ids()) + 1

    def _note_events(self) -> list[int]:
        pl = self._patterns_end()
        return [i for i in range(pl) if self.events[i][0] == EV_PATNOTES]

    def strip_notes(self, channels: set[int]) -> int:
        """Remove every note on the given channels from every pattern. Returns how many were removed."""
        removed = 0
        for i in self._note_events():
            v = self.events[i][1]
            keep = bytearray()
            for k in range(0, len(v) - NOTE_SIZE + 1, NOTE_SIZE):
                if struct.unpack("<H", v[k + 6 : k + 8])[0] in channels:
                    removed += 1
                else:
                    keep += v[k : k + NOTE_SIZE]
            self.events[i][1] = bytes(keep)
        return removed

    def add_pattern(self, pid: int, name: str, notes: bytes) -> None:
        """Insert a named pattern after the last existing pattern notes. A reused id would silently merge patterns, so it is refused."""
        if pid in self.pattern_ids():
            raise FlpError("pattern id %d already exists (ids must be unique across every part you add)" % pid)
        if pid >= MAX_PATTERN_ID:
            raise FlpError("pattern id %d too large" % pid)
        at = (self._note_events() or [self._patterns_end() - 1])[-1] + 1
        self.events[at:at] = [[EV_NEWPAT, struct.pack("<H", pid)], [EV_PATNAME, enc16(name)], [EV_PATNOTES, notes]]

    # ---- playlist
    def playlist_items(self) -> list[bytes]:
        return self._items(self.events[self._playlist_index()][1])

    def map_playlist(self, fn) -> int:
        """Replace every playlist item with fn(item_bytes) (same length). Returns how many items changed."""
        i = self._playlist_index()
        items = self.playlist_items()
        out = [fn(it) for it in items]
        if any(len(o) != len(a) for o, a in zip(out, items)):
            raise FlpError("map_playlist: items must keep their size")
        self.events[i][1] = b"".join(out)
        return sum(1 for a, b in zip(items, out) if a != b)

    def add_playlist_clips(self, clips: list[tuple[int, int, int, int]]) -> int:
        """Add pattern clips given as (pattern_id, start_bar, bars, track). Track is the playlist row counted from 0 at the top. Returns the item count."""
        items = self.playlist_items()
        tmpl = [it for it in items if struct.unpack("<H", it[6:8])[0] > PATTERN_BASE]
        if not tmpl and self.playlist_item_size() != len(PATTERN_CLIP_TEMPLATE):
            raise FlpError("no pattern clip to copy and this FL version's playlist items are not the 88-byte layout; re-save the project in FL 26")
        tmpl = tmpl or [PATTERN_CLIP_TEMPLATE]
        nid = max([0] + [struct.unpack("<I", it[32:36])[0] for it in items]) + 1
        for pid, bar, bars, track in clips:
            it = bytearray(tmpl[0])
            it[0:4] = struct.pack("<I", bar * TICKS_PER_BAR)
            it[6:8] = struct.pack("<H", PATTERN_BASE + pid)
            it[8:12] = struct.pack("<I", bars * TICKS_PER_BAR)
            it[12:14] = struct.pack("<H", 499 - track)
            it[32:36] = struct.pack("<I", nid)
            nid += 1
            items.append(bytes(it))
        items.sort(key=lambda it: struct.unpack("<I", it[0:4])[0])
        self.events[self._playlist_index()][1] = b"".join(items)
        return len(items)

    def pattern_lengths(self) -> dict[int, int]:
        """Length in ticks of each pattern as a clip plays it when its offsets are -1: its notes rounded up to whole bars, at least one bar
        (the same rule projmusic.song_notes uses to unroll looped clips)."""
        bar = self.ppq * 4
        out = {}
        for pid, notes in self.pattern_notes().items():
            last = max((n[0] + max(n[3], 1) for n in notes), default=0)
            out[pid] = max(bar, int(math.ceil(last / float(bar))) * bar)
        return out

    def window_playlist(self, start: int, end: int) -> dict:
        """Cut the current arrangement's playlist to ticks [start, end) and move that stretch to the song start, so a render of the file is
        only that stretch (a solo part's 16 bars instead of the whole song). Items wholly outside are removed; an item cut at either edge
        keeps the right content through its offsets, in each kind's unit: pattern clips in ticks (int, -1 is the whole pattern), automation
        clips in beats and audio clips in milliseconds at the project tempo (floats, -1 is from the start; a time-stretched audio clip is
        cut at the unstretched position). A pattern clip longer than its content window loops it; a cut one becomes one clip per pass, each
        inside the window, so no clip has to loop from a cut edge. Returns {"kept", "removed", "cut"}."""
        if end <= start:
            raise FlpError("window end must be after its start")
        i = self._playlist_index()
        items = self.playlist_items()
        ppq = self.ppq
        kinds: dict[int, int | None] = {}
        plen: dict[int, int] | None = None
        nid = max([0] + [struct.unpack("<I", it[32:36])[0] for it in items if len(it) >= 36]) + 1
        out, removed, cut = [], 0, 0
        for it in items:
            pos, = struct.unpack("<I", it[0:4])
            ref, = struct.unpack("<H", it[6:8])
            length, = struct.unpack("<I", it[8:12])
            if pos + length <= start or pos >= end:
                removed += 1
                continue
            a = max(pos, start)
            z = min(pos + length, end)
            shift, new_len = a - pos, z - a
            if not shift and new_len == length:
                b = bytearray(it)
                b[0:4] = struct.pack("<I", a - start)
                out.append(bytes(b))
                continue
            cut += 1
            if ref >= PATTERN_BASE:
                s0, e0 = struct.unpack("<ii", it[24:32])
                if s0 < 0 or e0 <= s0:
                    if plen is None:
                        plen = self.pattern_lengths()
                    s0, e0 = 0, plen.get(ref - PATTERN_BASE, self.ppq * 4)
                win = e0 - s0
                t, first = a, True
                while t < z:
                    c = s0 + (t - pos) % win
                    n = min(z - t, e0 - c)
                    b = bytearray(it)
                    b[0:4] = struct.pack("<I", t - start)
                    b[8:12] = struct.pack("<I", n)
                    b[24:32] = struct.pack("<ii", c, c + n)
                    if not first and len(b) >= 36:
                        b[32:36] = struct.pack("<I", nid)
                        nid += 1
                    out.append(bytes(b))
                    t += n
                    first = False
                continue
            if ref not in kinds:
                kinds[ref] = self.channel_type(ref) if ref in self.channel_ids() else None
            unit = 1.0 / ppq if kinds[ref] == 5 else 60000.0 / self.tempo() / ppq
            s0, _e0 = struct.unpack("<ff", it[24:32])
            s1 = (0.0 if s0 < 0 else s0) + shift * unit
            b = bytearray(it)
            b[0:4] = struct.pack("<I", a - start)
            b[8:12] = struct.pack("<I", new_len)
            b[24:32] = struct.pack("<ff", s1, s1 + new_len * unit)
            out.append(bytes(b))
        out.sort(key=lambda it: struct.unpack("<I", it[0:4])[0])
        self.events[i][1] = b"".join(out)
        return {"kept": len(out), "removed": removed, "cut": cut}

    def audio_item(self, ch: int) -> bytes:
        """The first playlist item that plays channel ch, to use as the layout for more clips of it (or of a clone)."""
        for it in self.playlist_items():
            if struct.unpack("<H", it[6:8])[0] == ch:
                return it
        raise FlpError("no playlist clip of channel %d to copy" % ch)

    def reset_playlist_tracks(self) -> int:
        """Every playlist row back to FL's plain state: enabled, not grouped, no icon, no name. A project saved after "Extract stems from
        sample" has its source row muted and the stem rows grouped and named (2026-10-29). Returns how many rows changed."""
        n, out = 0, []
        for e, v in self.events:
            if e == EV_TRACK_NAME:
                n += 1
                continue
            if e == EV_TRACK and len(v) > 46:
                b = bytearray(v)
                b[8:12], b[12], b[46] = bytes(4), 1, 0
                n += bytes(b) != bytes(v)
                v = bytes(b)
            out.append([e, v])
        self.events = out
        return n

    def clear_playlist(self) -> int:
        """Remove every playlist item. Returns how many there were."""
        i = self._playlist_index()
        n = len(self.playlist_items())
        self.events[i][1] = b""
        return n

    def add_audio_clips(self, ch: int, track: int, clips: list[tuple[int, int, float, float]], template: bytes) -> int:
        """Add audio clips of channel ch as (pos_ticks, length_ticks, start_ms, end_ms); track is the 0-based playlist row. The content window is
        start_ms to end_ms of the file; length_ticks should equal that window in ticks for normal speed. Returns the playlist item count."""
        items = self.playlist_items()
        nid = max([0] + [struct.unpack("<I", it[32:36])[0] for it in items]) + 1
        for pos, length, s_ms, e_ms in clips:
            it = bytearray(template)
            it[0:4] = struct.pack("<I", int(pos))
            it[6:8] = struct.pack("<H", ch)
            it[8:12] = struct.pack("<I", int(length))
            it[12:14] = struct.pack("<H", 499 - track)
            it[24:32] = struct.pack("<ff", s_ms, e_ms)
            it[32:36] = struct.pack("<I", nid)
            nid += 1
            items.append(bytes(it))
        items.sort(key=lambda it: (struct.unpack("<I", it[0:4])[0], struct.unpack("<I", it[32:36])[0]))
        self.events[self._playlist_index()][1] = b"".join(items)
        return len(items)

    def main_pitch(self) -> int:
        """The master pitch knob in cents (event 80, signed; PyFLP ProjectID.MainPitch): every instrument sounds this much off its notes.
        The Electroconductor demos sit at -400: notes in D minor that sound, and render, in Bb minor."""
        v = next((v for e, v in self.events if e == 80), None)
        if v is None:
            return 0
        return v if isinstance(v, int) else struct.unpack_from("<h", bytes(v), 0)[0]

    def tempo(self) -> float:
        """The project tempo in bpm."""
        for e, v in self.events:
            if e == EV_TEMPO and len(v) == 4:
                return struct.unpack("<I", v)[0] / 1000.0
        raise FlpError("no tempo event")

    def song_mode(self) -> bool:
        """True when the project plays the playlist (song mode); False in pattern mode, where a render covers one pattern only."""
        for e, v in self.events:
            if e == EV_LOOP_ACTIVE and len(v) == 1:
                return v[0] == 1
        raise FlpError("no play-mode event")

    def set_song_mode(self, on: bool = True) -> None:
        for ev in self.events:
            if ev[0] == EV_LOOP_ACTIVE and len(ev[1]) == 1:
                ev[1] = bytes([1 if on else 0])
                return
        raise FlpError("no play-mode event")

    def set_tempo(self, bpm: float) -> None:
        if not 20.0 <= bpm <= 999.0:
            raise FlpError("tempo out of range")
        for ev in self.events:
            if ev[0] == EV_TEMPO and len(ev[1]) == 4:
                ev[1] = struct.pack("<I", int(round(bpm * 1000)))
                return
        raise FlpError("no tempo event")

    def add_part(self, label: str, notes_by_bar: dict[int, bytes], track: int, base_id: int) -> dict[int, int]:
        """Add one pattern per distinct bar content and a one-bar clip per bar. Returns {bar: pattern_id}."""
        uniq: dict[bytes, int] = {}
        bar_pat: dict[int, int] = {}
        for bar in sorted(notes_by_bar):
            data = notes_by_bar[bar]
            if not data:
                continue
            if data not in uniq:
                uniq[data] = base_id + len(uniq)
                self.add_pattern(uniq[data], "%s %d" % (label, len(uniq)), data)
            bar_pat[bar] = uniq[data]
        self.add_playlist_clips([(pid, bar, 1, track) for bar, pid in bar_pat.items()])
        return bar_pat

    def add_part_blocks(self, label: str, notes_by_bar: dict[int, bytes], track: int, base_id: int, blocks: list[tuple[int, int, str]]) -> dict[int, int]:
        """Like add_part with piano rolls longer than a bar: blocks are (start bar, bars, name), such as a section of up to 16 bars. One
        pattern per distinct block content, named label + the block's name; its clip as long as its notes (whole bars, at most the block),
        since a clip longer than its pattern loops it. A note held past its block's end is cut there. Bars in no block get one-bar
        patterns. Returns {start bar: pattern_id}."""
        uniq: dict[bytes, int] = {}
        out: dict[int, int] = {}
        clips, covered = [], set()
        for start, n, name in blocks:
            recs, limit, last = [], n * TICKS_PER_BAR, 0
            for bar in range(start, start + n):
                covered.add(bar)
                data = notes_by_bar.get(bar) or b""
                for k in range(0, len(data) - NOTE_SIZE + 1, NOTE_SIZE):
                    rec = bytearray(data[k:k + NOTE_SIZE])
                    pos = struct.unpack_from("<I", rec, 0)[0] + (bar - start) * TICKS_PER_BAR
                    ln = min(struct.unpack_from("<I", rec, 8)[0], max(1, limit - pos))
                    struct.pack_into("<I", rec, 0, pos)
                    struct.pack_into("<I", rec, 8, ln)
                    recs.append(bytes(rec))
                    last = max(last, pos + max(ln, 1))
            if not recs:
                continue
            data = b"".join(recs)
            if data not in uniq:
                uniq[data] = base_id + len(uniq)
                self.add_pattern(uniq[data], "%s %s" % (label, name), data)
            out[start] = uniq[data]
            clips.append((uniq[data], start, min(n, max(1, -(-last // TICKS_PER_BAR))), track))
        rest = {b: d for b, d in notes_by_bar.items() if b not in covered and d}
        self.add_playlist_clips(clips)
        if rest:
            out.update(self.add_part(label, rest, track, base_id + len(uniq)))
        return out


def notes_by_bar(notes: list[tuple], channel: int) -> dict[int, bytes]:
    """Group (start_beat, dur_beats, key, vel[, pan]) notes into per-bar note bytes, positions relative to the bar."""
    return notes_by_bar_channels([(*n[:4], channel, *n[4:5]) for n in notes])


def notes_by_bar_channels(notes: list[tuple]) -> dict[int, bytes]:
    """Like notes_by_bar for several channels at once: rows are (start_beat, dur_beats, key, vel, channel[, pan]). One pattern can then hold a whole kit."""
    rows: dict[int, list[tuple[int, int, bytes]]] = {}
    for n in notes:
        st, dur, key, vel, channel = n[:5]
        pan = n[5] if len(n) > 5 else 64
        tick = int(round(st * TICKS_PER_BEAT))
        bar = tick // TICKS_PER_BAR
        pos = tick - bar * TICKS_PER_BAR
        ln = 0 if dur <= 0 else max(6, int(round(dur * TICKS_PER_BEAT)))
        rows.setdefault(bar, []).append((pos, key, note_bytes(pos, channel, key, ln, int(vel), int(pan))))
    return {b: b"".join(r[2] for r in sorted(v, key=lambda r: (r[0], r[1]))) for b, v in rows.items()}
