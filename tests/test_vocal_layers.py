"""The vocal-led layers recipe (the person, 2026-10-29): chords that follow the voice section by section, a held pad under spaced-out
stabs, a bass that rolls in the verses and holds longer notes when it drops, and piano rolls of up to 16 bars instead of a pattern a bar."""
from __future__ import annotations

import json

from coproducer import flpfile, remixbuild, remixplan, songanalysis, songplan, stylepack
from coproducer import voiceharmony as vh
from coproducer.testflp import remix_inputs

DATA = "tests/data/"
AM, F, C, G = (9, 0, 4), (5, 9, 0), (0, 4, 7), (7, 11, 2)


def _row(pcs) -> list[float]:
    row = [0.0] * 12
    for pc in pcs:
        row[pc] = 1.0
    return row


def test_each_section_kind_gets_the_chords_its_voice_sings():
    secs = [{"name": "intro", "start": 0, "end": 4}, {"name": "groove", "start": 4, "end": 12}, {"name": "drop", "start": 12, "end": 20}]
    verse, chorus = [AM, AM, F, F, C, C, G, G], [F, F, G, G, AM, AM, C, C]
    w = {4 + i: _row(p) for i, p in enumerate(verse)}
    w.update({12 + i: _row(p) for i, p in enumerate(chorus)})
    got = vh.section_loops(w, secs, 9, "minor")
    assert got["kinds"]["groove"]["chords"] == [9, 5, 0, 7] and got["kinds"]["drop"]["chords"] == [5, 7, 9, 0]
    assert got["bar_roots"][4:12] == [9, 9, 5, 5, 0, 0, 7, 7] and got["bar_roots"][12:20] == [5, 5, 7, 7, 9, 9, 0, 0]
    assert got["bar_roots"][:4] == [9, 9, 5, 5] and got["borrowed_from"] == "groove"      # the unsung intro takes the verse's loop
    assert got["qualities"] == {9: "min", 5: "maj", 0: "maj", 7: "maj"}


def test_the_pad_holds_each_chord_to_the_next_and_restrikes_in_builds():
    pack = {"pad": {"drop": "chord", "build": "bar", "voicing": "triad", "base": 48, "max_bars": 4}}
    secs = [{"name": "build", "start": 0, "end": 2}, {"name": "drop", "start": 2, "end": 12}]
    roots = [0, 0, 9, 9, 9, 9, 9, 9, 5, 5, 5, 5]
    ck = lambda pc, base=60: [base + pc, base + pc + 3, base + pc + 7]  # noqa: E731
    notes = stylepack.pad_notes(pack, secs, lambda b: roots[b], ck, 9, "minor")
    assert sorted({n[0] for n in notes}) == [0.0, 4.0, 8.0, 24.0, 32.0]   # build bars; A at bar 2, struck again after 4 bars; F at bar 8
    first = [n for n in notes if n[0] == 8.0]
    assert sorted(n[2] for n in first) == [57, 60, 64] and all(abs(n[1] - 16 * 0.97) < 1e-9 for n in first)
    assert stylepack.validate({**stylepack.load("house"), "pad": {"drop": "swell"}})[-1].startswith("pad.drop")


def test_piano_rolls_cover_whole_sections_and_clips_never_loop(tmp_path):
    (tmp_path / "sandbox").mkdir()
    inp = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
    f = flpfile.Flp.load(inp["base"])
    f.clear_playlist()
    phrase = [(0.0, 8.0, 60, 100), (12.0, 1.0, 62, 100)]                         # a 2-bar chord, a note in bar 3: 4 bars of content
    notes = phrase + [(32 + s, d, k, v) for s, d, k, v in phrase] + [(64.0, 40.0, 64, 100)]   # the same again at bar 8, a long note at bar 16
    ch = f.channel_ids()[0]
    got = f.add_part_blocks("Pad", flpfile.notes_by_bar(notes, ch), 3, f.next_pattern_id(1), [(0, 8, "Drop 1"), (8, 8, "Drop 2"), (16, 4, "Outro")])
    assert got[0] == got[8] and len(set(got.values())) == 2                      # identical sections share one piano roll
    clips = sorted(c for c in f.pattern_clips() if c[0] in got.values())
    assert [(pos // 384, ln // 384) for _p, pos, ln in sorted(clips, key=lambda c: c[1])] == [(0, 4), (8, 4), (16, 4)]
    lengths = f.pattern_lengths()
    assert all(ln <= lengths[p] for p, _pos, ln in clips)                         # no clip is longer than its pattern, so none loops
    assert max(n[3] for n in f.pattern_notes()[got[16]]) == 4 * 384              # the long note is cut at its section's end


def test_the_recipe_drafts_and_builds_a_pad_and_section_long_piano_rolls(tmp_path):
    words = json.load(open(DATA + "friends_vocal_words.json"))
    plan = songanalysis.draft_plan("friends_layers", songanalysis.tokens(words["words"]), source_bpm=108.478, key_pc=9, origin_s=27.3085,
                                   title="friends in low places", style="pop_dance", mode="major",
                                   variety={"seed": "layers", "lock": {"chords": "chords.pad_and_spaced_stabs", "bass": "bass.roll_then_long_drop"}})
    plan["pattern_bars"] = 16
    assert songplan.validate(plan) == [] and plan["style_overrides"]["pad"]["drop"] == "chord"
    songplan.apply(plan)
    try:
        (tmp_path / "sandbox").mkdir()
        inp = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
        out = str(tmp_path / "sandbox" / "layers.flp")
        rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], out, log=lambda *x: None)
        f = flpfile.Flp.load(out)
        spans = remixbuild.blocks(plan["sections"], 16)
        assert "pad" in rep["channel_ids"] and rep["pattern_counts"]["Pad"] >= 1
        assert all(n <= len(spans) for n in rep["pattern_counts"].values())
        clips, lengths = f.pattern_clips(), f.pattern_lengths()
        assert any(ln >= 8 * 384 for _p, _pos, ln in clips) and all(ln <= lengths[p] for p, _pos, ln in clips)
        drop = next(s for s in plan["sections"] if s["name"] == "drop")
        bass = [n for n in remixplan.reese_notes() if drop["start"] * 4 <= n[0] < drop["end"] * 4]
        verse = next(s for s in plan["sections"] if s["name"] == "groove")
        roll = [n for n in remixplan.reese_notes() if verse["start"] * 4 <= n[0] < verse["end"] * 4]
        held = sorted(n[1] for n in bass)
        assert held[len(held) // 2] > 1.0 > max(n[1] for n in roll[:12])          # mostly long notes when it drops, 16ths when it rolls
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))
