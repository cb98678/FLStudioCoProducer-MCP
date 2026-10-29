import numpy as np

from coproducer import bassnotes as B

RATE = 44100


def _tone(midi, secs):
    t = np.arange(int(secs * RATE)) / RATE
    f = 440 * 2 ** ((midi - 69) / 12)
    return 0.6 * np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)


def test_tracks_a_sequence_of_notes():
    seq = [(40, 0.5), (43, 0.5), (45, 0.5), (40, 0.5)]
    x = np.concatenate([_tone(m, s) for m, s in seq])
    t, m, lv = B.track_pitch(x, RATE)
    notes = B.notes_from_track(t, m, lv)
    assert [n["pitch"] for n in notes] == [40, 43, 45, 40]
    assert abs(notes[1]["start"] - 0.5) < 0.06 and abs(notes[1]["end"] - 1.0) < 0.06


def test_silence_gives_no_notes():
    t, m, lv = B.track_pitch(np.zeros(RATE), RATE)
    assert B.notes_from_track(t, m, lv) == []


def test_key_and_roots():
    # A minor walking bass: A A C D E E D C repeated
    seq = [(45, 0.5), (45, 0.5), (48, 0.5), (50, 0.5), (52, 0.5), (52, 0.5), (50, 0.5), (48, 0.5)] * 2
    x = np.concatenate([_tone(m, s) for m, s in seq])
    notes = B.notes_from_track(*B.track_pitch(x, RATE))
    k = B.estimate_key(notes)
    assert (k["tonic"], k["mode"]) in {("A", "minor"), ("C", "major")}
    roots = B.roots_per_bar(notes, 120.0, 0.0, 4)
    assert roots[0] == 9
