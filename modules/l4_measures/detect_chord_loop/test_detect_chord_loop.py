def bars(chords, repeats=2):
    notes = []
    for i, root_and_third_and_fifth in enumerate(chords * repeats):
        for p in root_and_third_and_fifth:
            notes.append({"pitch": p, "start": i * 4, "duration": 4, "velocity": 90})
    return notes


AM, F, C, G = (57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)


def test_finds_a_four_bar_loop(rig):
    r = rig.call("detect_chord_loop", notes=bars([AM, F, C, G]))
    assert r.ok and r.value["chords"] == ["Am", "F", "C", "G"] * 2
    assert r.value["loop"] == {"bars": 4, "progression": ["Am", "F", "C", "G"], "match": 1.0}
    assert rig.call("detect_chord_loop", notes=bars([AM, AM], repeats=4)).value["loop"]["bars"] == 1


def test_no_loop_and_empty(rig):
    r = rig.call("detect_chord_loop", notes=bars([AM, F, C, G, AM, G, F], repeats=1))
    assert r.value["loop"] is None
    assert rig.call("detect_chord_loop", notes=[]).value == {"chords": [], "loop": None}
