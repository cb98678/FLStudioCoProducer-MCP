def test_cleans_up(rig):
    notes = [{"pitch": 60, "start": 0, "duration": 1.0, "velocity": 90},
             {"pitch": 60, "start": 0.5, "duration": 1.0, "velocity": 90},     # overlaps the first: first is trimmed
             {"pitch": 62, "start": 2, "duration": 0.01, "velocity": 90},      # too short
             {"pitch": 64, "start": 2, "duration": 1, "velocity": 2},          # too quiet
             {"pitch": 65, "start": 1, "duration": 1}]
    r = rig.call("clean_midi_notes", notes=notes)
    assert r.ok and r.meta == {"removed": 2, "trimmed": 1}
    assert [(n["pitch"], n["start"], n["duration"]) for n in r.value] == [(60, 0, 0.5), (60, 0.5, 1.0), (65, 1, 1)]


def test_empty_and_bad_input(rig):
    assert rig.call("clean_midi_notes", notes=[]).value == []
    assert rig.call("clean_midi_notes", notes=[{"pitch": 60}]).error.code == "E_ARG"
