"""Support parts written as a session arranger would (arranger, skill session-arranger, 2026-11-06): the keys hold under a busy vocal and
move gently under a spacious one, the pad sits under her range and over the bass, the bass plays only its cells (plus approach notes
at phrase ends), the answer line only plays where she rests, velocities follow beat strength, and check() catches every broken rule."""
from __future__ import annotations

import numpy as np
from pathlib import Path

from coproducer import arranger as A

CHORDS = [{"bar": b + 1, "chord": c} for b, c in enumerate(["D", "A", "G", "A"] * 4)]


def busy_then_spacious() -> dict:
    """Bars 0-7: she sings 3 syllables a beat with a rest in bar 3; bars 8-15: one syllable every two beats, long rests."""
    sung = [False] * (16 * 16)
    ons = []
    for b in range(8):
        if b == 3:
            continue
        for st in range(16):
            sung[b * 16 + st] = st < 14
        ons += [b * 4 + i / 3 for i in range(12)]
    for b in range(8, 16):
        for st in range(0, 6):
            sung[b * 16 + st] = True
        ons += [b * 4, b * 4 + 2]
    return {"sung": sung, "onsets": sorted(ons), "floor_db": None}


def test_modes_follow_the_vocal_density():
    m = A.phrase_modes(busy_then_spacious(), 16)
    assert [x["mode"] for x in m[:3]] == ["hold"] * 3 and all(x["mode"] == "move" for x in m[4:])


def test_keys_hold_under_busy_and_move_under_spacious():
    vm = busy_then_spacious()
    kp = A.keys_parts(CHORDS, 16, A.phrase_modes(vm, 16), (62, 72))
    pad, keys = kp["pad"], kp["keys"]
    assert all(n[0] >= 32 for n in keys) and len(keys) == 8 * 8          # the figure only where she is spacious, 8ths
    held = [n for n in pad if n[0] < 32]
    assert min(n[1] for n in held) >= 3.9                                   # under the busy bars: a bar or more per chord
    assert max(n[2] for n in pad) <= 60 and min(n[2] for n in pad) >= 43   # under her low note (62 - 2), over the bass octave
    assert A.max_poly(pad) <= 4 and A.max_poly(keys) == 1


def test_an_unsure_third_is_left_out():
    ch = [{"bar": 1, "chord": "A", "margin": 0.04, "cands": ["A", "Am"]}, {"bar": 2, "chord": "D", "margin": 0.4, "cands": ["D", "Bm"]}]
    pad = A.keys_parts(ch, 2, [{"bars": [0, 2], "mode": "pulse"}], (64, 72))["pad"]
    bar1 = {n[2] % 12 for n in pad if n[0] == 0}
    bar2 = {n[2] % 12 for n in pad if n[0] == 4}
    assert 1 not in bar1 and 0 not in bar1 and {9, 4} <= bar1               # A sus2: no C#, no C
    assert {2, 6, 9} <= bar2


def test_bass_plays_its_cells_and_approaches_at_phrase_ends():
    cells = {b: ("halves" if b < 8 else "push") for b in range(16)}
    bass = A.bass_part(CHORDS, 16, cells.get, 2, "major")
    assert A.max_poly(bass) == 1
    allowed = {(b, st) for b, n in cells.items() for st, *_ in A.CELLS[n]} | {(b, 14) for b in cells}
    assert all((int(s // 4), int(round((s % 4) * 4))) in allowed for s, *_ in bass)
    app = [n for n in bass if abs(n[0] % 4 - 3.5) < 1e-6]
    assert {int(n[0] // 4) for n in app} == {3, 7, 11}                     # the 4th bar of each phrase (15 has no next chord)
    assert all(n[2] % 12 in A.MAJOR or (n[2] - 2) % 12 in A.MAJOR for n in app)
    assert all(36 <= n[2] <= 59 for n in bass) and all(36 <= n[2] <= 47 for n in bass if n[0] % 4 == 0)   # roots in the bass octave


def test_the_answer_plays_only_in_her_rests():
    vm = busy_then_spacious()
    notes, used = A.answer_part(CHORDS, 16, vm, (62, 72), 2, "major", every=1)
    assert notes and len(used) >= 4
    for s, d, *_ in notes:
        assert not any(vm["sung"][i] for i in range(int(s * 4), int(np.ceil((s + d) * 4))))
    assert all(n[2] >= 69 for n in notes) and A.max_poly(notes) == 1
    assert len({u["bar"] for u in used}) == len(used)                      # never two figures in one bar


def test_velocity_follows_beat_strength_and_is_not_flat():
    v = [A.velocity(b / 4, 1.0, "x") for b in range(16)]
    assert v[0] > v[8] > v[4] > v[2] > v[1] and max(v) < 127 and len(set(v)) > 4
    assert A.velocity(0.0, 1.0, "x") == A.velocity(0.0, 1.0, "x")         # fixed, not random run to run


def test_arrange_passes_its_own_check_and_check_catches_breaks():
    vm = busy_then_spacious()
    secs = [{"bars": [0, 8], "cell": "halves"}, {"bars": [8, 16], "cell": "push", "last": {"bars": 2, "cell": "eighths"}}]
    res = A.arrange(CHORDS, 16, vm, (62, 72), 2, "major", secs, answer_every=1)
    assert res["check"]["ok"], res["check"]["fails"]
    assert res["cells"][14] == "eighths" and res["cells"][13] == "push"
    bad = dict(res["parts"])
    bad["answer"] = bad["answer"] + [(1.0, 0.5, 74, 80)]                    # a note while she sings
    bad["bass"] = bad["bass"] + [(5.125, 0.25, 40, 90)]                     # off the 16th grid, outside the cells
    bad["pad"] = bad["pad"] + [(0.0, 4.0, k, 127) for k in (50, 52, 55)]    # six notes at once, at 127
    fails = " | ".join(A.check(bad, vm, res["cells"])["fails"])
    assert "answer: 1 notes while she sings" in fails and "bass: 1 starts off" in fails and "outside its cells" in fails
    assert "pad: 6 notes at once (limit 4)" in fails and "pad: flat or maxed" in fails


def test_vocal_map_from_audio_reads_rests():
    rate, bpm = 16000, 120.0
    t = np.arange(int(8.0 * rate)) / rate
    x = 0.3 * np.sin(2 * np.pi * 220 * t) * ((t % 2.0) < 1.0)              # sings the first half of every bar (a bar is 2 s)
    vm = A.vocal_map(x, rate, bpm, 0.0, 16)
    sung = np.array(vm["sung"]).reshape(4, 16)
    assert sung[:, :7].all() and not sung[:, 9:].any()
    assert A.gaps(vm, 1.0)[:2] == [(2.0, 4.0), (6.0, 8.0)]


def test_chord_names_parse():
    assert A.parse_chord("F#m") == (6, "min") and A.parse_chord("Bb") == (10, "maj") and A.parse_chord("D/F#") == (2, "maj")
    assert A.parse_chord("Bdim") == (11, "dim") and A.parse_chord(None) is None


def test_a_plan_carries_the_arranged_parts_onto_the_build_channels():
    """A plan's support_parts replace the style's pad, stabs, bass and arp; an arranged bass silences the sub; a bad entry is refused."""
    from coproducer import remixplan, songplan
    base = songplan.load("plans/friends_in_low_places.json")
    vm = busy_then_spacious()
    res = A.arrange(CHORDS, 16, vm, (62, 72), 2, "major", [{"bars": [0, 16], "cell": "halves"}], answer_every=1)
    plan = dict(base, support_parts={k: [list(n) for n in v] for k, v in res["parts"].items()})
    assert songplan.validate(plan) == []
    assert any("support_parts" in e for e in songplan.validate(dict(base, support_parts={"lead": [[0, 1, 60, 90]]})))
    songplan.apply(plan)
    try:
        assert remixplan.pad_notes()[:3] == [tuple(n) for n in res["parts"]["pad"]][:3]
        assert remixplan.reese_notes()[0] == tuple(res["parts"]["bass"][0]) and remixplan.sub_notes(remixplan.drums()) == []
        assert remixplan.arp_notes() == [tuple(n) for n in res["parts"]["answer"]]
        assert remixplan.stab_notes()[0] == tuple(res["parts"]["keys"][0])
    finally:
        songplan.apply(base)
    assert remixplan.SUPPORT_PARTS == {}


def test_a_guide_melody_keeps_her_main_notes_only():
    """Her line with ornaments (quick 16th turns around each held note): the guide keeps the held notes, at most two a bar, on 8ths."""
    sung = []
    for b in range(4):
        for half, k in ((0, 66), (2, 69)):
            t = b * 4 + half
            sung += [[t, 0.25, k + 2, 80], [t + 0.25, 0.25, k + 1, 80], [t + 0.5, 1.25, k, 90]]   # a turn into the held note
    g = A.guide_melody(sung, 2, "major")
    assert len(g) <= 8 and A.max_poly(g) == 1 and all(abs(n[0] * 2 - round(n[0] * 2)) < 1e-9 for n in g)
    assert [n[2] for n in g][:2] == [66, 69] and all(n[2] % 12 in {(2 + s) % 12 for s in A.MAJOR} for n in g)
    assert A.check({"guide": g}, {"sung": [True] * 64, "onsets": []})["ok"]


def test_a_remix_build_runs_the_support_pass(tmp_path):
    """A drafted house plan with support band_guide: the build reads the vocal on the remix grid, fits the pack's parts, adds the guide to
    the arp channel and reports the check; support off builds the pack's parts as written."""
    import json

    import soundfile as sf

    from coproducer import remixbuild, remixplan, songanalysis, songplan
    from coproducer.testflp import remix_inputs
    words = json.load(open("tests/data/friends_vocal_words.json"))
    plan = songanalysis.draft_plan("friends_house", songanalysis.tokens(words["words"]), source_bpm=108.478, key_pc=9, origin_s=27.3085,
                                   title="friends in low places", style="house", variety={"seed": "sup", "history": []}, mode="major")
    plan["support"] = {"mode": "band_guide"}
    assert songplan.validate(plan) == []
    assert any("support" in e for e in songplan.validate(dict(plan, support={"mode": "loud"})))
    songplan.apply(plan)
    try:
        (tmp_path / "sandbox").mkdir()
        inp = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
        rate, secs = 22050, 400.0
        t = np.arange(int(secs * rate)) / rate
        voice = 0.3 * np.sin(2 * np.pi * 330 * t) * ((t % 4.0) < 2.5)        # a sung note in every 4 s, 2.5 s long
        sf.write(str(Path(inp["audio"]) / ("vocals_%d.wav" % round(remixplan.BPM))), voice, rate)
        logs = []
        rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], str(tmp_path / "sandbox" / "s.flp"), log=lambda *x: logs.append(" ".join(map(str, x))))
        assert rep["support"] is not None and "Arp" in rep["pattern_counts"]
        assert any(l.startswith("support pass: pack parts fitted") and "guide" in l for l in logs)
        st = remixbuild.support_state(json.load(open(Path(inp["audio"]) / "techhouse_audio.json")), inp["audio"], remixplan.ORIGIN_S, log=lambda *x: None)
        assert st["guide"] and all(n[2] % 12 in {(9 + s) % 12 for s in A.MAJOR} for n in st["guide"])
        arp = remixbuild.part_notes("arp", st)
        assert all(g in arp for g in [tuple(n) for n in st["guide"]])
        plan["support"] = {"mode": "off"}
        songplan.apply(plan)
        assert remixplan.SUPPORT == {} and remixbuild.support_state({}, inp["audio"], 0.0) is None
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))


def test_her_instruments_go_under_every_sung_clip():
    plan = {"vocal_clips": [[8, 0, 10.0, 20.0, "Verse 1", "phrase", "vocals"], [24, 8, 30.0, 40.0, "Chorus 1", "phrase", "vocals"],
                            [24, 8, 30.0, 40.0, "Original chorus", "bars", "other"]], "clip_words": [{}, {}, {}]}
    assert A.with_original(plan) == 1
    assert plan["vocal_clips"][-1][6] == "other" and plan["vocal_clips"][-1][0] == 8 and len(plan["clip_words"]) == 4
    assert A.with_original(plan) == 0
