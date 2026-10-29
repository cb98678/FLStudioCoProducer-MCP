NOTES = [{"pitch": 60, "start": 0, "duration": 1}, {"pitch": 48, "start": 0, "duration": 4},
         {"pitch": 64, "start": 1, "duration": 1}, {"pitch": 64, "start": 2, "duration": 0.5},
         {"pitch": 62, "start": 2.5, "duration": 1.5}]


def test_extracts_the_top_line(rig):
    r = rig.call("extract_melody_contour", notes=NOTES)
    assert r.value["pitches"] == [60, 64, 64, 62] and r.value["steps"] == [4, 0, -2]
    assert r.value["gaps"] == [1.0, 1.0, 0.5] and r.value["contour"] == "URD"
    assert rig.call("extract_melody_contour", notes=NOTES, voice="bottom").value["pitches"][0] == 48


def test_empty_list(rig):
    assert rig.call("extract_melody_contour", notes=[]).error.code == "E_ARG"
