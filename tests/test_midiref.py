"""Reference MIDI files (src/coproducer/midiref.py): tested against the record before use, chords read cleanly, the strum found."""
import mido
import pytest

from coproducer import midiref

PROG = [9, 9, 11, 4] * 8  # A A B E, 32 bars


def _file(tmp_path, transpose=0, wrong=False, melody=True):
    m = mido.MidiFile(ticks_per_beat=96)
    for name, prog, ch, fn in (("Bass", 33, 1, "bass"), ("Accoustic Guitar", 25, 2, "gtr"), ("Piano", 0, 0, "mel"), ("Drums", 0, 9, "dr")):
        t = mido.MidiTrack()
        m.tracks.append(t)
        t.append(mido.MetaMessage("track_name", name=name))
        t.append(mido.Message("program_change", program=prog, channel=ch))
        ev = []
        for b, r in enumerate(PROG):
            r = (r + (5 if wrong and b % 2 else 0) + transpose) % 12
            third = 3 if (r - transpose) % 12 == 11 else 4
            if fn == "bass":
                ev.append((b * 384, 380, 24 + r, 90))
            elif fn == "gtr":
                for st in (0, 144, 192):
                    ev += [(b * 384 + st, 30, 48 + (r + i) % 12, 80) for i in (0, third, 7)]
            elif fn == "mel" and melody:
                ev += [(b * 384 + k * 96, 90, 72 + (r + 4 * k) % 12, 70) for k in range(4)]
            elif fn == "dr":
                ev += [(b * 384 + k * 96, 20, 36, 100) for k in range(4)]
        msgs = sorted([(t0, "on", p, v) for t0, d, p, v in ev] + [(t0 + d, "off", p, 0) for t0, d, p, v in ev])
        now = 0
        for t0, kind, p, v in msgs:
            t.append(mido.Message("note_on" if kind == "on" else "note_off", note=p, velocity=v, channel=ch, time=t0 - now))
            now = t0
    path = tmp_path / "ref.mid"
    m.save(str(path))
    return str(path)


def _audio(offset=4):
    return {b - offset: r for b, r in enumerate(PROG)}


def test_a_matching_file_is_accepted_and_read_cleanly(tmp_path):
    m = midiref.read(_file(tmp_path))
    assert [t["role"] for t in m["tracks"]] == ["bass", "harmony", "harmony", "drums"]
    fit = midiref.fit(m, _audio(), 9, 108.5)
    assert fit["accepted"] and fit["root_match"] == 1.0 and fit["offset_bars"] == 4 and fit["transpose"] == 0
    q = midiref.chord_qualities(m)
    assert q == {9: "maj", 11: "min", 4: "maj"}                                 # the melody above E4 does not blur the thirds
    assert midiref.strum(m) == "X.....X.X......."
    assert midiref.voicing(11, "min") == [59, 62, 66] and midiref.voicing(4, "5") == [59, 64]


def test_a_transposed_file_is_turned_back(tmp_path):
    m = midiref.read(_file(tmp_path, transpose=2))
    fit = midiref.fit(m, _audio(), 9, 108.5)
    assert fit["accepted"] and fit["transpose"] == 10 and midiref.chord_qualities(m, fit["transpose"])[11] == "min"


def test_a_wrong_file_is_refused_with_the_reason(tmp_path):
    m = midiref.read(_file(tmp_path, wrong=True))
    fit = midiref.fit(m, _audio(), 9, 108.5)
    assert not fit["accepted"] and "bass roots agree" in fit["why"]


def test_unreadable(tmp_path):
    bad = tmp_path / "x.mid"
    bad.write_bytes(b"not midi")
    with pytest.raises((OSError, ValueError, EOFError)):
        midiref.read(str(bad))


def test_a_double_tempo_file_with_a_sung_bass_voice():
    """MIDI World's "Girls": notated at twice the record's tempo, no bass track, the roots in a low backing voice singing root and fifth."""
    m = {"tpb": 96, "beats_per_bar": 4, "tempo_bpm": 280.0, "tracks": [
        {"name": "Voice", "program": 60, "channel": 4, "role": "other",
         "notes": [n for b in range(24) for n in (((b * 8, b * 8 + 3.5, 53 if b % 2 == 0 else 50, 90)), (b * 8 + 4, b * 8 + 7.5, 48 if b % 2 == 0 else 45, 90))]}]}
    assert midiref.bar_beats(m, 140.0) == 8
    audio = {b: (5 if b % 2 == 0 else 2) for b in range(24)}
    f = midiref.fit(m, audio, 5, 140.0)
    assert f["accepted"] and f["transpose"] == 0 and f["bar_beats"] == 8     # F and D: the lower of a root and fifth pair is the root
