def line(pitches, gaps=None):
    t, out = 0.0, []
    for i, p in enumerate(pitches):
        out.append({"pitch": p, "start": t, "duration": 0.5})
        t += (gaps or [1.0] * len(pitches))[i]
    return out


MELODY = line([60, 62, 64, 62, 67, 65, 64, 60])


def test_scores_similar_and_different(rig):
    same = rig.call("compare_note_sequences", a=MELODY, b=MELODY).value
    assert same["overall"] == 1.0
    moved = rig.call("compare_note_sequences", a=MELODY, b=line([p + 7 for p in [60, 62, 64, 62, 67, 65, 64, 60]])).value
    assert moved["melody"] == 1.0 and moved["rhythm"] == 1.0 and moved["onsets"] == 1.0 and moved["pitch_class"] < 1.0
    other = rig.call("compare_note_sequences", a=MELODY, b=line([61, 70, 50, 83, 40, 99, 55, 66], [0.5, 0.75, 2, 0.25, 1, 1.5, 0.5, 1])).value
    assert other["overall"] < 0.4 < moved["overall"]
    chords = MELODY + [{"pitch": p - 12, "start": 0, "duration": 4} for p in (60, 64, 67)]
    assert rig.call("compare_note_sequences", a=MELODY, b=chords).value["melody"] == 1.0   # top line unchanged


def test_empty_input(rig):
    assert rig.call("compare_note_sequences", a=[], b=MELODY).error.code == "E_ARG"
