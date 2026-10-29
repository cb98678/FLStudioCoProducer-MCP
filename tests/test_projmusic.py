"""projmusic, the demo study's reader (2026-10-28): it unrolls looped pattern clips into song notes, names the roles, finds the key and the
chords, writes a drum voice's groove as a 16th pattern (or a triplet one) and splits the song into sections."""
from __future__ import annotations

import struct

from coproducer import flpfile as F
from coproducer import projmusic as P
from coproducer.testflp import project


def test_drum_voices_come_from_whole_words_and_substrings():
    assert P.drum_voice("Grv Kick 18") == "kick" and P.drum_voice("Attack Clap 19") == "clap"
    assert P.drum_voice("808 Snare") == "snare" and P.drum_voice("Collider Slack OHat 02") in ("ohat", "hat")
    assert P.drum_voice("Reverse Pad") is None                        # "verse" inside a word is not a section and "rev" is not a drum


def test_groove_reads_the_pattern_the_lateness_and_triplets():
    four = [(b * 4.0 + k, 0, 60, 0.25, 100) for b in range(4) for k in range(4)]
    g = P.groove(four)
    assert g["pattern"] == "X...X...X...X..." and g["bars"] == 4 and g["late_16ths"] == 0.0 and g["triplet_share"] == 0.0
    swung = [(b * 4.0 + k + 0.5 + 0.083, 0, 60, 0.25, 100) for b in range(4) for k in range(4)]
    assert P.groove(swung)["late_16ths"] > 0.3                        # hits a third of a 16th behind the grid
    trip = [(b * 4.0 + k / 3.0, 0, 60, 0.2, 100) for b in range(2) for k in range(12)]
    t = P.groove(trip)
    assert t["triplet_share"] >= 0.6 and t["triplet_pattern"] == "XXXXXXXXXXXX"


def test_key_chords_and_roman_numerals():
    roles = {1: "chords"}
    am = [(0.0, 1, k, 4.0, 100) for k in (57, 60, 64)] + [(4.0, 1, k, 4.0, 100) for k in (53, 57, 60)] + [(8.0, 1, k, 4.0, 100) for k in (55, 59, 62)]
    key = P.find_key({1: am * 4}, roles)
    assert key["key"] in ("A minor", "C major")
    assert P.chords_per_bar({1: am}, roles, 3) == ["Am", "F", "G"]
    assert P.roman("F", 9, "minor") == "bVI" and P.roman("Dm7", 9, "minor") == "iv7"


def test_looped_pattern_clips_unroll_into_song_time():
    f = project({0: "Pluck"}, {0: [0, 96]}, bars=1)
    it = bytearray(f.playlist_items()[0])
    it[8:12] = struct.pack("<I", 384 * 3)                           # a one-bar pattern clip stretched over three bars: it loops
    f.events[f._playlist_index()][1] = bytes(it)
    notes = P.song_notes(f)[0]
    assert [n[0] for n in notes] == [0.0, 1.0, 4.0, 5.0, 8.0, 9.0]


def test_a_clip_muted_in_the_playlist_plays_nothing():
    """Item flag 0x2000 is a muted clip (the demo songs: every solo whose clips all carried it rendered silent): its notes are not song notes."""
    f = project({0: "Pluck"}, {0: [0, 96]}, bars=1)
    it = bytearray(f.playlist_items()[0])
    assert not F.Flp.item_muted(bytes(it)) and len(f.pattern_clips()) == 1
    flags = struct.unpack_from("<H", it, F.ITEM_FLAGS_AT)[0]
    struct.pack_into("<H", it, F.ITEM_FLAGS_AT, flags | F.ITEM_MUTED)
    f.events[f._playlist_index()][1] = bytes(it)
    assert F.Flp.item_muted(bytes(it)) and f.pattern_clips() == [] and len(f.pattern_clips(muted=True)) == 1
    assert P.song_notes(f) == {}


def test_segment_merges_phrases_and_keeps_marker_names():
    act = [{"roles": {"drums"}, "notes": 8}] * 8 + [{"roles": {"drums", "bass", "chords"}, "notes": 30}] * 16
    secs = P.segment(act, [])
    assert [s["start_bar"] for s in secs] == [1, 9] and secs[1]["energy"] == 1.0
    named = P.segment(act, [{"bar": 1, "name": "Intro"}, {"bar": 9, "name": "Drop 1"}])
    assert [s["name"] for s in named] == ["Intro", "Drop 1"]


def test_roll_shows_notes_and_holds():
    notes = [(0.0, 1, 57, 1.0, 100), (1.0, 1, 69, 0.25, 100)]
    row = P.roll(notes, 1, 1)[0].split()
    assert row[0] == "A3" and row[1] == "-" and row[4] == "A4"
    assert F.TICKS_PER_BAR == 384


def test_the_master_pitch_moves_the_key_and_chords_it_sounds_in():
    """The Electroconductor demos are written in D minor with the master pitch at -400 cents: they sound, and render, in Bb minor."""
    key = {"key": "D minor", "tonic": 2, "mode": "minor", "confidence": 0.9}
    k, ch = P.sounding(key, ["Dm7", "Fmaj7", None, "Bbmaj7", "G7"], -400)
    assert k["key"] == "Bb minor" and k["written"] == "D minor" and k["tonic"] == 10 and k["master_pitch_cents"] == -400
    assert ch == ["Bbm7", "C#maj7", None, "F#maj7", "Eb7"]
    assert P.roman("Bbm7", 10, "minor") == P.roman("Dm7", 2, "minor")      # roman numerals do not move
    assert P.sounding(key, ["Dm7"], 0) == (key, ["Dm7"])
    f = project({0: "Pluck"}, {0: [0, 96]}, bars=1)
    assert f.main_pitch() == 0
    f.events.insert(1, [80, struct.pack("<h", -400)])
    assert f.main_pitch() == -400
