"""Small synthetic FL projects for tests of the inspection helpers (no FL needed)."""
from __future__ import annotations

import struct

from coproducer import flpfile as F

# A sampler's levels (pan, volume, pitch 0 cents, filter) and parameter block (pitch range 2 semitones at byte 112) as FL 26 saves them.
LEVELS = struct.pack("<6i", 6400, 10000, 0, 256, 0, 0)
PARAMS = bytes.fromhex("ffffffff0000000001000001ffffffff3c0000000000803f0000803f0000803f0000803f0000803f0000000001000000ffffffff000400003000000000000100a705"
                       "0000000000000001000000000000000000000000000000000000010000000000000000000000000000000000000002000000feffffffffffffff00000000000000"
                       "0000000000000000000000f03f0000000000000000ffffffff01000000000000000000e03f")


def project(channels: dict[int, str], notes: dict[int, list[int]], bpm: float = 120.0, bars: int = 2, presets: dict[int, str] | None = None, samples: dict[int, str] | None = None) -> F.Flp:
    """channels {id: name}; notes {channel id: [tick positions in a one-bar pattern]}; the pattern plays for `bars` bars from bar 0."""
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, len(channels), 96)
    ev = [[199, F.enc16("26.1.7")], [156, struct.pack("<I", int(bpm * 1000))], [9, b"\x01"]]
    for c, name in channels.items():
        ev += [[64, struct.pack("<H", c)], [0, b"\x01"], [203, F.enc16(name)], [104, struct.pack("<H", 3)], [219, LEVELS], [215, PARAMS]]
        if samples and c in samples:
            ev.append([196, F.enc16(samples[c])])
        if presets and c in presets:
            ev.append([213, b'XferJson\0{"component":"controller","presetName":"%s"}' % presets[c].encode()])
    ev += [[99, b"\x00\x00"], [233, b""]]
    f = F.Flp(head, ev, b"")
    data = b"".join(F.note_bytes(t, c, 60) for c, ticks in notes.items() for t in ticks)
    f.add_pattern(1, "P", data)
    f.add_playlist_clips([(1, 0, bars, 1)])
    return f


def with_mixer(f: F.Flp, tracks: int = 16) -> F.Flp:
    """Add a mixer state event with a volume record for tracks 0..tracks-1 (what set_mixer_volume edits)."""
    rec = b"".join(struct.pack("<IHHI", 0, F.MIXER_VOLUME, 0x7000 + 64 * t, 12800) for t in range(tracks))
    at = [i for i, (e, _v) in enumerate(f.events) if e == F.EV_ARRANGEMENT][0]
    f.events.insert(at, [F.EV_MIXER, rec])
    return f


def remix_inputs(tmp, plan_chops: dict, echoed: tuple) -> dict:
    """Write a tiny base (stem) project, a Sytrus project and an audio folder with techhouse_audio.json under tmp; return their paths.
    plan_chops is the plan's chop table; the audio json gets a file entry and a short duration for every chop and echo."""
    import json
    from pathlib import Path

    tmp = Path(tmp)
    base = project({0: "808 Kick", 1: "song_vocals"}, {0: [0]}, bpm=108.0, bars=1, samples={0: "kick.wav", 1: "song_vocals.wav"})
    base.add_audio_clips(1, 1, [(0, 384, 0.0, 1000.0)], F.PATTERN_CLIP_TEMPLATE)
    with_mixer(base).save(str(tmp / "base.flp"))
    with_mixer(project({0: "Remix Sub", 1: "Trance pluck", 2: "Trance pluck #2"}, {})).save(str(tmp / "sytrus.flp"))
    audio = tmp / "audio"
    audio.mkdir()
    chops = {n: {"file": "CP_Chop_%s.wav" % n, "dur_s": 1.0, **({"orig_start_s": float(v["start"]), "orig_end_s": float(v["end"])}
                                                              if isinstance(v, dict) and "start" in v else {})}
             for n, v in (plan_chops.items() if isinstance(plan_chops, dict) else ((n, None) for n in plan_chops))}
    chops.update({n + "_echo": {"file": "CP_Chop_%s_echo.wav" % n, "dur_s": 1.6} for n in echoed})
    from . import remixplan  # clips sit just after their original bar line, as the real ones do

    clips = []
    for _rb, ob, *rest in remixplan.VOCAL_CLIPS:
        t = remixplan.ORIGIN_S + ob * 240.0 / remixplan.SOURCE_BPM + 0.2
        clips.append({"orig_start_s": t, "orig_end_s": t + 4.0, "stem": rest[4] if len(rest) > 4 else "vocals"})
    (audio / "techhouse_audio.json").write_text(json.dumps({"stretch": 1.14, "delay_s": 0.0, "chops": chops, "clips": clips}), encoding="utf-8")
    return {"base": str(tmp / "base.flp"), "sytrus": str(tmp / "sytrus.flp"), "audio": str(audio)}


def with_organization(f: F.Flp, inserts: int = 4, rows: int = 3) -> F.Flp:
    """Give a synthetic project what the organizer edits: a colour and a group on every channel, two channel rack groups, mixer insert blocks 1..inserts
    (routing, output, icon and name events as FL writes them) and playlist track records 1..rows."""
    ev = f.events
    for i in reversed([i for i, (e, _v) in enumerate(ev) if e == 203]):
        ev[i + 1 : i + 1] = [[128, bytes((92, 101, 106, 0))], [41, b"\x00"], [145, struct.pack("<i", 0)]]
    first = [i for i, (e, _v) in enumerate(ev) if e == 64][0]
    ev[first:first] = [[231, F.enc16("Audio")], [231, F.enc16("Unsorted")]]
    at = [i for i, (e, _v) in enumerate(ev) if e == F.EV_ARRANGEMENT][0]
    new = []
    for _ in range(inserts):
        new += [[235, b"\x01"], [147, b"\xff\xff\xff\xff"], [42, b"\x00"], [95, b"\x00\x00"], [204, F.enc16("Insert")]]
    new.append([47, b"\x00"])
    ev[at:at] = new
    pl = [i for i, (e, _v) in enumerate(ev) if e == F.EV_PLAYLIST][0]
    tracks = []
    for k in range(1, rows + 1):  # FL writes each row record, then its flag event 43, after the arrangement's playlist
        tracks += [[238, struct.pack("<I", k) + bytes(66)], [43, b"\x00"]]
    ev[pl + 1 : pl + 1] = tracks
    return f


def with_second_arrangement(f: F.Flp, name: str = "Alt", current: bool = True) -> F.Flp:
    """Copy the arrangement section (playlist, rows, markers) as a second arrangement with id 1 and, when current, mark it current
    (event 100), as FL 26 does for a project with two arrangements."""
    ev = f.events
    a = [i for i, (e, _v) in enumerate(ev) if e == F.EV_ARRANGEMENT][0]
    b = next((i for i, (e, _v) in enumerate(ev) if e == F.EV_ARR_CURRENT), None)
    b = b if b is not None else next((i for i in range(a + 1, len(ev)) if ev[i][0] not in (F.EV_PLAYLIST, 238, 239, 43, 148, 205, F.EV_ARR_NAME)), len(ev))
    sec = [[e, bytes(v)] for e, v in ev[a:b]]
    sec[0] = [F.EV_ARRANGEMENT, struct.pack("<H", 1)]
    sec = [x for x in sec if x[0] != F.EV_ARR_NAME]
    sec.insert(1, [F.EV_ARR_NAME, F.enc16(name)])
    ev[b:b] = sec
    if current:
        ev[b + len(sec) : b + len(sec)] = [[F.EV_ARR_CURRENT, struct.pack("<H", 1)]]
    return f
