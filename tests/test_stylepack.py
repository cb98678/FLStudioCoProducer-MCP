"""Style packs: every pack loads and cites its sources, the grammar writes the genre's signature rhythm, and a song plan with a style builds a
project whose parts follow the pack (2026-10-25). The tech-house plan without a style still builds through the old engine."""
from __future__ import annotations

import json

import pytest

from coproducer import drumplan, flpfile, remixbuild, remixplan, songanalysis, songplan, stylepack
from coproducer.testflp import remix_inputs

DATA = "tests/data/"


def _steps(plan: drumplan.Plan, inst: str, bar: int) -> list[float]:
    return sorted(s for b, s, i, *_ in plan.events if i == inst and b == bar)


def test_every_pack_is_valid_and_cites_sources():
    assert set(stylepack.names()) >= {"tech_house", "house", "techno", "dubstep", "dnb", "trap"}
    for n in stylepack.names():
        p = stylepack.load(n)
        assert p["sources"] and stylepack.validate(p) == []
    with pytest.raises(stylepack.StyleError):
        stylepack.load("polka")
    bad = dict(stylepack.load("dubstep"), drums={"drop": {"bars": {"cowbell": "x..............."}}})
    assert any("unknown voice" in m for m in stylepack.validate(bad))


def test_signature_rhythms():
    secs = [{"name": "drop", "start": 0, "end": 8}]
    dub = stylepack.drums(stylepack.load("dubstep"), secs)
    assert _steps(dub, "snare", 0) == [8.0] and _steps(dub, "kick", 0) == [0.0, 10.0]          # half time: snare on 3
    dnb = stylepack.drums(stylepack.load("dnb"), secs)
    assert 4.0 in _steps(dnb, "snare", 0) and 12.0 in _steps(dnb, "snare", 0) and _steps(dnb, "kick", 0) == [0.0, 10.0]
    techno = stylepack.drums(stylepack.load("techno"), secs)
    assert _steps(techno, "kick", 0) == [0.0, 4.0, 8.0, 12.0]
    trap = stylepack.drums(stylepack.load("trap"), secs)
    hats = _steps(trap, "hat", 0)
    assert any(s % 1 for s in hats)                                                             # 32nd-note hat rolls
    assert _steps(dub, "kick", 7) == [0.0] and _steps(dub, "snare", 7) == []                     # the drop's last bar breaks down


def test_tempo_strategy():
    assert stylepack.vocal_multiple(174, 108.478) == 1.0 and stylepack.vocal_multiple(140, 108.478) == 1.0   # x0.80 half time: far too slow
    assert stylepack.vocal_multiple(70, 140) == 2.0 and stylepack.vocal_multiple(230, 108.0) == 0.5


def test_pick_tempo_keeps_the_voice_at_most_a_little_slower():
    """The person (2026-10-28): a vocal may run slower, "but not too slow and preserve pitch": never more than 6 % slower."""
    for name in stylepack.names():
        pack = stylepack.load(name)
        for src in (84.0, 96.5, 108.504, 120.0, 128.0, 130.0, 140.0, 174.0):
            bpm = stylepack.pick_tempo(pack, src)
            assert stylepack.stretch_of(bpm, stylepack.vocal_multiple(bpm, src), src) >= stylepack.MAX_SLOWDOWN - 1e-9, (name, src, bpm)
    assert stylepack.pick_tempo(stylepack.load("house"), 130.0) == 126                # 3 % slower beats leaving house's range
    assert stylepack.pick_tempo(stylepack.load("house"), 140.0) == 140.0              # 10 % slower is too slow: the song's own tempo
    assert stylepack.vocal_multiple(126, 130.0) == 1.0 and stylepack.stretch_cost(0.90) == float("inf")
    assert stylepack.pick_tempo(stylepack.load("techno"), 108.504) == 126            # the tempo in range that speeds the voice up least
    assert stylepack.pick_tempo(stylepack.load("hiphop"), 108.504) == 108.504        # out of range, but no rushed voice
    assert stylepack.pick_tempo(stylepack.load("dnb"), 108.504) == 170               # follow false: drum and bass stays drum and bass
    assert stylepack.pick_tempo(stylepack.load("house"), 120.0) == 120.0             # in range: untouched


def _draft(style: str, variety=False) -> dict:
    """The pack as written (variety off): these tests pin each pack's own parts; tests/test_variety.py covers the per-song choices."""
    words = json.load(open(DATA + "friends_vocal_words.json"))
    return songanalysis.draft_plan("friends_" + style, songanalysis.tokens(words["words"]), source_bpm=108.478, key_pc=9, origin_s=27.3085,
                                   title="friends in low places", style=style, variety=variety)


@pytest.mark.parametrize("style", ["dubstep", "techno", "dnb", "trap", "house", "deep_house", "nu_disco"])
def test_a_styled_plan_builds(style, tmp_path):
    plan = _draft(style)
    assert songplan.validate(plan) == [] and plan["style"] == style
    pack = stylepack.load(style)
    assert plan["bpm"] == stylepack.pick_tempo(pack, 108.478) and plan["bpm"] * plan["vocal_multiple"] >= 108.478 * stylepack.MAX_SLOWDOWN
    assert plan["arrangement"] == "song" and plan["sections"][0] == {"name": "intro", "start": 0, "end": dict(pack["sections"])["intro"]}
    vocal = [c for c in plan["vocal_clips"] if c[6] == "vocals"]
    assert [c[4] for c in vocal] == ["Verse 1", "Chorus 1", "Verse 2 into the chorus", "Chorus 2"]   # whole verses and choruses, in the song's order
    for c in vocal:                                                                          # each one fills its section from the bar it starts on
        sec = next(x for x in plan["sections"] if x["start"] == c[0])
        part = next(p for p in plan["form"] if p["bar0"] == c[1])
        assert sec["end"] - sec["start"] >= part["bar1"] - part["bar0"]
    assert any(c[6] == "other" for c in plan["vocal_clips"])                                 # the original's instrumentation plays too
    assert all(len(v["words"].split()) >= 3 or v["end_mode"] == "phrase" for k, v in plan["chops"].items() if k != "stutter")   # whole phrases
    assert plan["stutter"]["chop"] == "stutter" and plan["stutter"]["bars"]   # the roll into the last drop
    songplan.apply(plan)
    try:
        assert remixplan.STYLE["name"] == style and abs(remixplan.STRETCH - plan["bpm"] * plan["vocal_multiple"] / 108.478) < 1e-9
        inp = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
        (tmp_path / "sandbox").mkdir()
        out = str(tmp_path / "sandbox" / (style + ".flp"))
        rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], out, log=lambda *a: None)
        f = flpfile.Flp.load(out)
        names = {f.channel_info(c)["name"] for c in f.channel_ids()}
        assert f.tempo() == plan["bpm"] and rep["pattern_counts"]["Drums"] > 0
        vocal_ch = rep["channel_ids"]["vocal"]
        roll = [c for c in f.audio_clips() if c["channel"] == vocal_ch and c["length"] < 4 * 96 * 0.3]
        assert len(roll) == 7 and roll[0]["length"] > roll[-1]["length"]           # the stutter: seven hits, each shorter
        assert pack["bass_sample"]["label"] in names and "Original Instruments" in names
        if not pack.get("sub"):
            assert "Sub Bass" not in names                     # no sub line in this style: no empty channel
        if not pack.get("chords"):
            assert "Chord Stab" not in names
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))
    assert remixplan.STYLE is None


def test_the_first_song_plan_still_uses_the_tech_house_engine():
    songplan.apply(songplan.load("plans/friends_in_low_places.json"))
    assert remixplan.STYLE is None and remixplan.PITCH_RATIO == 0.99424 and remixplan.STRETCH == 124.0 / 108.478


def test_every_style_names_a_valid_production_recipe_and_targets():
    from pathlib import Path

    from coproducer import production
    for n in stylepack.names():
        pack = stylepack.load(n)
        recipe = production.load_recipe(pack["production_recipe"])
        assert production.check_recipe(recipe) == [], (n, production.check_recipe(recipe))
        assert Path(pack["targets"]).is_file(), pack["targets"]
    assert production.check_recipe({"pump": [{"on": "nowhere"}], "transitions": {"drop>moon": [{"recipe": "warp", "on": "music_bus"}]}})


def test_deep_house_and_nu_disco_carry_their_signatures():
    """Added 2026-10-26 for songs house and techno do not fit: sad and romantic songs (deep house), happy and playful ones (nu-disco)."""
    secs = [{"name": "drop", "start": 0, "end": 4}, {"name": "build", "start": 4, "end": 12}]
    deep, disco = stylepack.load("deep_house"), stylepack.load("nu_disco")
    d = stylepack.drums(deep, secs)
    assert _steps(d, "kick", 0) == [0.0, 4.0, 8.0, 12.0] and _steps(d, "clap", 0) == [4.0, 12.0] and not _steps(d, "snare", 6)   # no snare roll
    n = stylepack.drums(disco, secs)
    assert _steps(n, "snare", 0) == [4.0, 12.0] and any(abs(s - 15.0) < 0.2 for s in _steps(n, "ohat", 3))   # the open hat doubles at the end of bar 4 (swung)
    assert disco["bass"]["groove"] == "x.o.x.o.x.o.x.o."                                          # the octave disco bass
    assert deep["drums"]["swing"] > 0.5 and stylepack.pick_tempo(deep, 108.478) == 118 and stylepack.pick_tempo(disco, 108.478) == 112


def test_packs_are_found_by_the_songs_mood():
    assert stylepack.for_mood(["sad", "romantic"])[0] == {"style": "deep_house", "matched": ["sad", "romantic"]}
    assert stylepack.for_mood(["Playful", "comic"])[0]["style"] == "nu_disco"
    assert {r["style"] for r in stylepack.for_mood(["angry"])} == {"dubstep", "techno"}
    assert stylepack.for_mood(["serene"]) == [] and stylepack.for_mood([]) == []
    assert all(stylepack.load(n).get("moods") for n in stylepack.names())                   # every pack says which moods it serves
