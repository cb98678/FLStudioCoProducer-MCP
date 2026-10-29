NOTES = [{"pitch": 60, "start": 0.07, "duration": 0.9}, {"pitch": 62, "start": 0.52, "duration": 0.1}]


def test_snaps_to_grid(rig):
    r = rig.call("quantize_notes", notes=NOTES, grid_beats=0.25)
    assert [n["start"] for n in r.value] == [0.0, 0.5] and [n["duration"] for n in r.value] == [0.9, 0.1]
    half = rig.call("quantize_notes", notes=NOTES, grid_beats=0.25, strength=0.5).value
    assert [n["start"] for n in half] == [0.035, 0.51]
    q = rig.call("quantize_notes", notes=NOTES, grid_beats=0.25, quantize_length=True).value
    assert [n["duration"] for n in q] == [1.0, 0.25]


def test_rejects_bad_grid(rig):
    assert rig.call("quantize_notes", notes=NOTES, grid_beats=0).error.code == "E_ARG"
    assert rig.call("quantize_notes", notes=[{"pitch": 200, "start": 0, "duration": 1}]).error.code == "E_ARG"
