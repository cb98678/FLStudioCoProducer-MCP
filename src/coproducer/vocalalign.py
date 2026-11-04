"""Put a singer's clips in line with the project's grid without cutting a word (skill vocal-slice-align, the person's ask of 2026-11-02).

A recorded singer keeps time to her own beat (her strums, warped onto a steady grid by tools/warp_to_grid.py), and her syllables sit a
few tens of milliseconds ahead of it (Hello Toni: 30 ms). Dragging a slice until its first syllable hits a grid line, which is what a
person does by eye, puts the pickup on the beat and the stressed syllable a 16th early. The measured rule instead:

* a phrase (a clip at least PHRASE_BEATS of her beats long) moves by the smallest amount that puts her beats on the project's beats, and
  her even beats on beats 1 and 3 of the bar when the phrase is CHORD_BEATS or longer (her chords change every two beats, so the stabs
  and her melody then agree), plus her lead (newtimeview.best_lead), so her onsets land on the 16ths;
* a riff (shorter) keeps the feel the person chose: its first onset snaps to the nearest 16th;
* a throw (a clip on another mixer track whose window lies inside a phrase's window, placed where that material plays) follows its phrase;
* clips of one channel whose windows touch in the file and continue in the playlist are one phrase (slicing a held word helps nothing);
  identical clips on one mixer track play once; a shorter clip overlapping the same material within a beat on the same mixer track is a
  flam and goes.

Positions are FL clip positions in ticks; windows are the file's own milliseconds (the channel plays the file at its own speed on FL's
Stretch, so one of her beats is one project beat, see flpfile.set_stretch). This module is arithmetic over clip records, so the tests run
without audio; tools/align_vocal_clips.py brings the onsets (newtimeview.onset_times) and the slice files' places in the long file.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from . import flpfile

PHRASE_BEATS = 3.0     # a clip this long in her beats is a phrase; shorter is a riff
CHORD_BEATS = 8.0      # from here on her two-beat chord grid is matched too
TOUCH_S = 0.03         # windows closer than this in the file are contiguous
TOUCH_BEATS = 0.2      # ...when their playlist positions continue within this
FLAM_BEATS = 1.0       # the same material playing at the same time (within a beat) on one mixer track is a flam
LIVE = ("phrase", "riff", "throw")


@dataclass
class Clip:
    channel: int
    pos: int              # ticks
    length: int           # ticks
    start_s: float        # window in the long vocal file, seconds
    end_s: float
    row: int
    mixer: int
    kind: str = ""        # phrase, riff, throw; or dup, flam, merged (gone)
    new_pos: int | None = None
    shift_beats: float = 0.0
    note: str = ""
    merged: list = field(default_factory=list)

    def beats(self, source_bpm: float) -> float:
        return (self.end_s - self.start_s) * source_bpm / 60.0


def her_beat(t_s: float, source_bpm: float, origin_s: float) -> float:
    """Where a time of the file sits on the singer's own beat grid."""
    return (t_s - origin_s) * source_bpm / 60.0


def collect(f: flpfile.Flp, offsets: dict[int, float], mixers: dict[int, int]) -> list[Clip]:
    """The vocal clips of the project. offsets maps each vocal channel to where its file starts in the long vocal file (0 for the long
    file itself, the located offset for a slice file); mixers maps each channel to its mixer track."""
    out = []
    for it in f.playlist_items():
        ch = struct.unpack_from("<H", it, 6)[0]
        if ch not in offsets:
            continue
        s_ms, e_ms = struct.unpack_from("<ff", it, 24)
        off = offsets[ch]
        out.append(Clip(ch, struct.unpack_from("<I", it, 0)[0], struct.unpack_from("<I", it, 8)[0], off + s_ms / 1000.0, off + e_ms / 1000.0,
                        499 - struct.unpack_from("<H", it, 12)[0], mixers.get(ch, 0)))
    out.sort(key=lambda c: (c.pos, c.mixer, c.start_s))
    return out


def dedupe(clips: list[Clip], ppq: int, source_bpm: float) -> list[Clip]:
    """Identical clips on one mixer track play once; the shorter of two clips on one mixer track that play the same material at the same
    time (within a beat) is a flam or a forgotten copy under a slice, and goes."""
    seen: dict = {}
    for c in clips:
        key = (c.mixer, c.pos, round(c.start_s, 3), round(c.end_s, 3))
        if key in seen:
            c.kind, c.note = "dup", "the same clip as the one on channel %d" % seen[key].channel
        else:
            seen[key] = c
    live = [c for c in clips if not c.kind]
    for a in live:
        for b in live:
            if a is b or a.kind or b.kind or a.mixer != b.mixer:
                continue
            same = min(a.end_s, b.end_s) - max(a.start_s, b.start_s) > 0.3
            near = abs((a.pos - b.pos) / ppq - (a.start_s - b.start_s) * source_bpm / 60.0) < FLAM_BEATS   # the same material at the same time
            if same and near and (a.end_s - a.start_s) < (b.end_s - b.start_s):
                a.kind, a.note = "flam", "its material already plays in the longer clip at %.2f beats" % (b.pos / ppq)
    return clips


def merge_contiguous(clips: list[Clip], source_bpm: float, ppq: int) -> list[Clip]:
    """Clips of one channel whose windows touch in the file and whose positions continue in the playlist become one clip."""
    out: list[Clip] = []
    for c in sorted(clips, key=lambda c: (c.channel, c.start_s)):
        prev = next((p for p in reversed(out) if p.channel == c.channel and not p.kind), None) if not c.kind else None
        if prev is not None and abs(c.start_s - prev.end_s) <= TOUCH_S:
            expect = prev.pos + (c.start_s - prev.start_s) * source_bpm / 60.0 * ppq
            if abs(c.pos - expect) <= TOUCH_BEATS * ppq:
                prev.end_s = c.end_s
                prev.merged.append(c.pos)
                c.kind, c.note = "merged", "joined to the clip at %.2f beats (its window followed on)" % (prev.pos / ppq)
        out.append(c)
    out.sort(key=lambda c: (c.pos, c.mixer, c.start_s))
    return out


def first_onset(onsets, start_s: float, end_s: float, edge_s: float = 0.012) -> float | None:
    """The first onset inside a window; a cut made at a waveform's start counts (within edge_s of the window start)."""
    for o in onsets:
        if start_s - edge_s <= o < end_s:
            return float(o)
    return None


def plan_moves(clips: list[Clip], onsets, source_bpm: float, origin_s: float, ppq: int, lead_s: float = 0.0,
               phrase_beats: float = PHRASE_BEATS, chord_beats: float = CHORD_BEATS) -> list[Clip]:
    """Decide every live clip's new position (ticks). onsets: the long file's onset times in seconds."""
    lead_b = lead_s * source_bpm / 60.0
    k = source_bpm / 60.0
    live = [c for c in clips if not c.kind]
    for c in live:   # phrases and riffs
        pos_b = c.pos / ppq
        if c.beats(source_bpm) >= phrase_beats:
            c.kind = "phrase"
            d = pos_b - her_beat(c.start_s, source_bpm, origin_s)   # the project beat where her beat 0 would land
            unit = 2.0 if c.beats(source_bpm) >= chord_beats else 1.0
            shift = round(d / unit) * unit - d + lead_b
            c.note = "her beats on the project's beats%s, plus her %.0f ms lead" % (" and her chord grid on beats 1 and 3" if unit == 2 else "", lead_s * 1000)
        else:
            c.kind = "riff"
            on = first_onset(onsets, c.start_s, c.end_s)
            on = c.start_s if on is None else on
            ob = pos_b + (on - c.start_s) * k
            shift = round(ob * 4) / 4.0 - ob
            c.note = "its first onset (%.3f s of the file) on the nearest 16th" % on
        c.new_pos = max(0, int(round((pos_b + shift) * ppq)))
    phrases = [c for c in live if c.kind == "phrase"]
    for c in live:   # throws follow the phrase they were cut from
        for p in phrases:
            if p.mixer == c.mixer or p is c or not (p.start_s - 0.02 <= c.start_s and c.end_s <= p.end_s + 0.02):
                continue
            if abs((c.pos - p.pos) / ppq - (c.start_s - p.start_s) * k) < 1.0:
                c.kind = "throw"
                c.new_pos = max(0, int(round(p.new_pos + (c.start_s - p.start_s) * k * ppq)))
                c.note = "follows the phrase at %.2f beats (mixer track %d)" % (p.pos / ppq, p.mixer)
                break
    for c in live:
        c.shift_beats = round((c.new_pos - c.pos) / ppq, 4)
        c.length = int(round(c.beats(source_bpm) * ppq))
    return clips


def apply(f: flpfile.Flp, clips: list[Clip], rows: dict[int, int], channel_of: dict[int, int], template: bytes, vocal_channels: set[int]) -> dict:
    """Rewrite the project's vocal clips: every clip of the vocal channels goes; the live ones come back at their new positions, on the
    playlist row and the channel chosen per mixer track (rows[mixer], channel_of[mixer]), with windows in the long file's ms."""
    removed = f.remove_playlist_items(lambda it: struct.unpack_from("<H", it, 6)[0] not in vocal_channels)
    groups: dict = {}
    for c in clips:
        if c.kind in LIVE:
            groups.setdefault((channel_of[c.mixer], rows[c.mixer]), []).append((c.new_pos, c.length, c.start_s * 1000.0, c.end_s * 1000.0))
    for (ch, row), items in groups.items():
        f.add_audio_clips(ch, row, items, template)
    return {"removed": removed, "added": sum(len(v) for v in groups.values())}


def report(clips: list[Clip], ppq: int) -> list[dict]:
    return [{"channel": c.channel, "mixer": c.mixer, "kind": c.kind, "pos_beats": round(c.pos / ppq, 4),
             "new_pos_beats": (round(c.new_pos / ppq, 4) if c.new_pos is not None else None), "shift_beats": c.shift_beats,
             "window_s": [round(c.start_s, 4), round(c.end_s, 4)], "merged_from_beats": [round(m / ppq, 4) for m in c.merged], "note": c.note}
            for c in sorted(clips, key=lambda c: (c.pos, c.mixer))]
