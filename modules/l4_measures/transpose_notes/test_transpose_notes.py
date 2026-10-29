NOTES = [{"pitch": 60, "start": 0, "duration": 1, "velocity": 90}, {"pitch": 67, "start": 1, "duration": 1}]


def test_shifts_pitches(rig):
    r = rig.call("transpose_notes", notes=NOTES, semitones=-5)
    assert r.ok and [n["pitch"] for n in r.value] == [55, 62] and r.value[0]["velocity"] == 90
    assert [n["pitch"] for n in rig.call("transpose_notes", notes=NOTES, semitones=70, fold_octaves=True).value] == [118, 125]


def test_out_of_range(rig):
    r = rig.call("transpose_notes", notes=NOTES, semitones=70)
    assert not r.ok and r.error.code == "E_ARG" and r.error.detail["pitch"] == 60
    assert rig.call("transpose_notes", notes=NOTES, semitones=200).error.code == "E_ARG"
