"""Slide notes, the sampled-note lead and the captured drum loop (the Better Off Alone / Pickle study, 2026-10-29)."""
import struct

import numpy as np
import soundfile as sf

from coproducer import flpfile, remixbuild, remixplan, songplan
from coproducer.testflp import remix_inputs


def test_a_slide_note_carries_the_slide_flag_and_starts_no_note():
    plain, slide = flpfile.note_bytes(0, 3, 60, 96), flpfile.note_bytes(0, 3, 62, 12, slide=True)
    assert struct.unpack_from("<H", plain, 4)[0] == 0x4000 and struct.unpack_from("<H", slide, 4)[0] == 0x4008
    by = flpfile.notes_by_bar_channels([(0, 0.125, 64, 100, 3, 64, True), (0, 1, 63, 100, 3)])
    keys = [(struct.unpack_from("<H", by[0], k + 4)[0], struct.unpack_from("<H", by[0], k + 12)[0]) for k in range(0, len(by[0]), 24)]
    assert keys == [(0x4000, 63), (0x4008, 64)]            # the note first, then the slide that bends it
    assert flpfile.notes_by_bar([(0, 1, 60, 90, 64, True)], 2)[0] == flpfile.note_bytes(0, 2, 60, 96, 90, 64, True)


def test_the_lead_keeps_the_melody_and_bends_only_its_phrase_starts():
    lead = {"sample": "x.wav", "root_midi": 71, "notes": [[0, 0.5, 71, 100], [0.5, 0.5, 68, 90], [2, 1.5, 76, 110], [3.5, 0.25, 75, 100]]}
    rows = remixplan.sampler_lead_notes(lead)
    main = [r for r in rows if not r[5]]
    assert [r[0] for r in main] == [0, 0.5, 2, 3.5]
    assert [r[2] for r in main] == [59, 57, 64, 64]          # phrase starts one semitone low (scooped); the rest as written (key = midi - 71 + 60)
    slides = [r for r in rows if r[5]]
    assert [(r[0], r[1], r[2]) for r in slides] == [(0, 0.125, 60), (2, 0.125, 65)]
    long_fall = remixplan.sampler_lead_notes({**lead, "scoop": {"when": "none"}, "fall": {"semitones": 2, "beats": 0.25, "min_dur": 1.0}})
    assert [(r[0], r[2]) for r in long_fall if r[5]] == [(3.25, 63)]   # only the 1.5-beat note falls, two semitones in its last quarter beat
    assert remixplan.sampler_lead_notes({}) == []


def test_a_drum_loop_plays_once_per_loop_in_its_sections():
    remixplan.SECTIONS = [{"name": "intro", "start": 0, "end": 8, "label": "DJ Intro"}, {"name": "break", "start": 8, "end": 16},
                          {"name": "drop", "start": 16, "end": 22}]
    got = remixplan.drum_loop_notes({"sample": "loop.wav", "bars": 2, "sections": ["DJ Intro", "drop"], "vel": 90})
    assert [n[0] / 4 for n in got] == [0, 2, 4, 6, 16, 18, 20] and got[-1][1] == 8 and {n[2] for n in got} == {60}
    assert remixplan.drum_loop_notes({}) == []
    plan = {"drum_loops": [{"sample": "a.wav"}, {"sample": "b.wav", "bars": 2}]}
    assert [d["sample"] for d in songplan.drum_loops(plan)] == ["a.wav", "b.wav"] and songplan.drum_loops({"drum_loop": {"sample": "c"}}) == [{"sample": "c"}]


def test_the_plan_checks_the_new_parts():
    plan = songplan.load("plans/friends_in_low_places.json")
    plan["sampler_lead"] = {"notes": [[0, 1, 200, 100]], "scoop": {"when": "sometimes"}}
    plan["drum_loop"] = {"sample": "l.wav", "bars": 3}
    bad = " ".join(songplan.validate(plan))
    assert "needs a sample (WAV path)" in bad and "[start beat, length beats, MIDI note, velocity]" in bad and "scoop when" in bad and "bars 1, 2, 4 or 8" in bad


def test_the_build_puts_the_lead_and_the_loop_on_samplers(tmp_path):
    plan = songplan.load("plans/friends_in_low_places.json")
    rate = 44100
    t = np.arange(int(0.4 * rate)) / rate
    sf.write(str(tmp_path / "note.wav"), 0.3 * np.sin(2 * np.pi * 493.88 * t), rate)
    sf.write(str(tmp_path / "loop.wav"), np.zeros(int(1.9 * rate)), rate)
    plan["sampler_lead"] = {"sample": str(tmp_path / "note.wav"), "root_midi": 71, "label": "Lead - Pickle Note",
                            "notes": [[32 * 4, 0.5, 71, 100], [32 * 4 + 0.5, 0.5, 68, 90]]}
    plan["drum_loops"] = [{"sample": str(tmp_path / "loop.wav"), "bars": 1, "sections": ["intro"]},
                          {"sample": str(tmp_path / "loop.wav"), "bars": 2, "sections": ["drop"], "label": "Perc - Top Loop"}]
    songplan.apply(plan)
    inputs = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
    (tmp_path / "sandbox").mkdir()
    out = str(tmp_path / "sandbox" / "lead.flp")
    rep = remixbuild.build(inputs["base"], inputs["sytrus"], inputs["audio"], out, log=lambda *a: None)
    f = flpfile.Flp.load(out)
    names = {f.channel_info(c)["name"]: c for c in f.channel_ids()}
    lead, loop, top = names["Lead - Pickle Note"], names["Perc - Drum Loop"], names["Perc - Top Loop"]
    assert f.channel_info(lead)["sample"].endswith("note.wav") and f.channel_info(loop)["sample"].endswith("loop.wav")
    assert f.note_ticks(lead) == [32 * 384, 32 * 384 + 48]                  # the slide note starts no note
    allnotes = [n for ns in f.pattern_notes().values() for n in ns if n[1] == lead]
    assert sorted(n[2] for n in allnotes) == [57, 59, 60]                    # B4 scooped from A#4 (key 59 then a slide to 60), G#4 as written
    assert f.note_ticks(loop) == [b * 384 for b in range(8)] and f.note_ticks(top) and f.note_ticks(top)[0] == 40 * 384
    assert rep["pattern_counts"]["Lead"] >= 1 and rep["pattern_counts"]["Drum Loop"] >= 1
    songplan.apply(songplan.load("plans/friends_in_low_places.json"))


def test_a_glide_starts_on_the_last_notes_pitch_while_it_still_rings():
    """The Pickle lead: every note within a beat of a different one slides from it in about 22 ms; after a rest or on a repeat, no slide."""
    lead = {"sample": "x.wav", "root_midi": 60, "glide": {"beats": 0.05}, "scoop": {"when": "none"},
            "notes": [[0, 0.5, 71, 100], [0.5, 0.5, 68, 100], [1.0, 0.5, 68, 100], [4.0, 0.5, 75, 100]]}
    rows = remixplan.sampler_lead_notes(lead)
    assert [(r[0], r[2], r[5]) for r in rows] == [(0, 71, False), (0.5, 71, False), (0.5, 68, True), (1.0, 68, False), (4.0, 75, False)]
    assert [r[1] for r in rows if r[5]] == [0.05]


def test_a_plans_bass_note_keys_the_bass_part(tmp_path):
    """A plan's bass_sample (one G#1 cut from a record) plays its own pitch on key 60: the bass part keys from it, not from the A1 default."""
    from coproducer import remixaudio
    plan = songplan.load("plans/friends_in_low_places.json")
    plan["bass_sample"] = {"file": str(tmp_path / "b.wav"), "root_midi": 32, "label": "Pedal Bass"}
    songplan.apply(plan)
    try:
        assert remixplan.BASS_SAMPLE_PC == 8 and remixplan.reese_key(8) == 60 and remixplan.reese_key(9) == 61 and remixplan.reese_key(6) == 58
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))
    assert remixplan.BASS_SAMPLE_PC == 9 and remixplan.BASS_SAMPLE == {}
    sf.write(str(tmp_path / "r48.wav"), np.zeros((4800, 2)), 48000)
    assert len(remixaudio._at_rate(str(tmp_path / "r48.wav"), 44100)) == 4410
    bad = songplan.validate({**songplan.load("plans/friends_in_low_places.json"), "bass_sample": {"root_midi": 32}})
    assert any("bass_sample needs a file" in b for b in bad)
