"""The variety engine and its option bank (2026-10-28): every option is valid data the engine can realize, choices follow the song's brief and
change from remix to remix, a plan carries them, and the build plays them (form, groove, bass, chords, arp, kit, demo instruments)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from coproducer import arrange, flpfile, fxbed, production, remixbuild, remixplan, songanalysis, songform, songplan, stylepack, variety
from coproducer.testflp import remix_inputs

DATA = "tests/data/"
BANK = variety.load_bank()
STUDY = Path(__file__).resolve().parents[1] / "docs" / "demo_study" / "data"


def test_every_option_is_described_sourced_and_unique():
    ids = [o["id"] for opts in BANK.values() for o in opts]
    assert len(ids) == len(set(ids))
    assert set(BANK) >= {"form", "drums", "kit", "bass", "chords", "arp", "harmony", "sound", "fx", "mix", "vocal", "automation"}
    songs = variety.sources()
    for cat, opts in BANK.items():
        assert len(opts) >= 6, cat
        for o in opts:
            assert o["id"].startswith(cat + ".") and o["label"] and o["what"] and isinstance(o.get("genres"), list), o["id"]
            assert "—" not in o["what"] + o["label"] + o.get("how", "")          # the person's rule for written text: no em dashes
            for s in o.get("sources", []):
                assert s["song"] in songs, (o["id"], s)


def test_every_pattern_option_overlays_a_valid_pack():
    house = stylepack.load("house")
    for cat in ("form", "drums", "bass", "chords", "arp"):
        for o in BANK[cat]:
            p = variety.apply_overrides(house, variety.overrides({"choices": {cat: o["id"]}}, BANK))
            assert stylepack.validate(p) == [], (o["id"], stylepack.validate(p))


def test_every_production_move_is_a_valid_recipe_move():
    for cat in ("fx", "mix", "automation"):
        for o in BANK[cat]:
            r = variety.merge_recipe(production.load_recipe("techno"), variety.production_patch({"choices": {cat: o["id"]}}, BANK))
            assert production.check_recipe(r) == [], (o["id"], production.check_recipe(r))


def test_fx_policies_place_renderable_cues():
    secs = [{"name": "intro", "start": 0, "end": 8}, {"name": "groove", "start": 8, "end": 24}, {"name": "build", "start": 24, "end": 32},
            {"name": "drop", "start": 32, "end": 48}, {"name": "break", "start": 48, "end": 56}, {"name": "outro", "start": 56, "end": 64}]
    for o in BANK["fx"]:
        cues = arrange.generate_fx_cues(secs, variety.fx_policy({"choices": {"fx": o["id"]}}, BANK))
        for c in cues:
            t0, x = fxbed.cue_audio(c, 0.5)
            assert x.ndim == 2 and len(x) > 0 and t0 >= -4
    quiet = arrange.generate_fx_cues(secs, {"into_build": [], "into_drop": [{"kind": "sub_drop", "bar": 0, "seconds": 2.0}]})
    assert not any(c["kind"] in ("noise_riser", "tone_riser") and c["bar"] == 24 for c in quiet)   # the build's risers are gone
    assert any(c["kind"] == "sub_drop" and c["bar"] == 32 for c in quiet)
    assert any(c["kind"] == "downlifter" and c["bar"] == 48 for c in quiet)                        # moments the policy leaves keep the default


def test_kits_harmony_and_sounds_point_at_real_things():
    for o in BANK["kit"]:
        for v, path in o["engine"]["voices"].items():
            assert v in stylepack.VOICES and path.lower().endswith((".wav", ".wv", ".ogg", ".flac", ".mp3"))
    for o in BANK["harmony"]:
        loop = o["engine"].get("loop")
        assert loop is None or len(loop) == 8
        for entry in loop or []:    # one chord a bar, or two with the 16th step where the second starts
            chords = [entry[0], entry[1]] if isinstance(entry[0], list) else [entry]
            assert all(0 <= off < 12 and q in songanalysis_qualities() for off, q in chords), (o["id"], entry)
            assert not isinstance(entry[0], list) or 1 <= entry[2] <= 15
    for o in BANK["sound"]:
        imp = o["engine"]["import"]
        assert o["engine"]["role"] in variety.SOUND_ROLES and imp["channels"]
        d = json.loads((STUDY / (imp["flp"] + ".json")).read_text(encoding="utf-8"))
        assert set(imp["channels"]) <= {p["channel"] for p in d["parts"]}


def songanalysis_qualities() -> set:
    return {"min", "maj", "min7", "maj7", "dom7", "sus2", "sus4", "add9", "madd9", "power", "minmaj7", "six", "min6"}


BRIEF = {"style": "house", "moods": ["happy", "warm"], "energy": "mid", "bpm": 124, "has_roots": True}


def test_choices_are_reproducible_follow_the_brief_and_honour_locks():
    a, b = variety.choose(BRIEF, seed="friends"), variety.choose(BRIEF, seed="friends")
    assert a == b
    assert a["choices"]["harmony"] == "harmony.keep_original"                          # the record's chords are kept
    genres = variety.genres_for("house")
    core = ("drums", "bass", "kit", "chords", "arp")                                   # where the genre lives (forms follow the song's mood)
    fits = [cat for cat in core if set(variety.find(BANK, a["choices"][cat])["genres"]) & (genres | {"*"})]
    assert len(fits) >= len(core) - 1                                                  # all fit the genre but the one surprise
    c = variety.choose(BRIEF, seed="friends", lock={"drums": "drums.dembow", "sound.arp": "sound.tinke_bell"}, surprise=False)
    assert c["choices"]["drums"] == "drums.dembow" and c["sounds"]["arp"] == "sound.tinke_bell" and c["surprise"] is None
    with pytest.raises(variety.VarietyError):
        variety.choose(BRIEF, seed="x", lock={"drums": "drums.polka"})


def test_locked_sounds_count_toward_the_number_of_sounds():
    """Locking every choice of a remix rebuilds that remix: no extra demo instrument joins the locked ones (2026-10-28)."""
    first = variety.choose(BRIEF, seed="lockme")
    lock = {**first["choices"], **{"sound.%s" % k: v for k, v in first["sounds"].items()}}
    again = variety.choose(BRIEF, seed="other", lock=lock, history=[{"choices": first["choices"], "sounds": first["sounds"]}])
    assert again["choices"] == first["choices"] and again["sounds"] == first["sounds"]


def test_history_makes_the_next_remix_different():
    """The complaint this answers: every remix had the same form, groove and parts. With the last remixes in the history, a new song's
    choices change in most categories, and across ten songs no full set repeats."""
    history: list[dict] = []
    seen = []
    for k in range(10):
        r = variety.choose(BRIEF, seed="song%d" % k, history=history)
        seen.append(tuple(sorted(r["choices"].items())))
        if history:
            last = history[0]["choices"]
            assert sum(r["choices"][c] != last[c] for c in r["choices"] if c != "harmony") >= 5
        history.insert(0, {"choices": r["choices"], "sounds": r["sounds"]})
    assert len(set(seen)) == 10
    assert len({dict(s)["form"] for s in seen}) >= 4 and len({dict(s)["drums"] for s in seen}) >= 4


def test_history_file_round_trip(tmp_path):
    p = tmp_path / "variety_history.json"
    assert variety.load_history(p) == []
    variety.record(p, "a", {"choices": {"form": "form.journey"}, "sounds": {}})
    variety.record(p, "b", {"choices": {"form": "form.lofi_loop"}, "sounds": {}})
    assert [h["name"] for h in variety.load_history(p)] == ["b", "a"]                # most recent first
    assert variety.record(p, "a", {"choices": {"form": "form.journey"}, "sounds": {}}) == 2     # a rebuild of the same plan replaces its row
    assert variety.record(p, "a", {"choices": {"form": "form.mid8_ramp"}, "sounds": {}}) == 3   # another version of the song is remembered too
    assert [h["choices"]["form"] for h in variety.load_history(p)][:2] == ["form.mid8_ramp", "form.journey"]


def _form_parts():
    words = json.load(open(DATA + "friends_vocal_words.json"))
    toks = songform.good(songanalysis.tokens(words["words"]))
    return songform.form(toks, "friends in low places", 27.3085, 240.0 / 108.478), toks


@pytest.mark.parametrize("oid,builds,breaks", [("form.edm_two_drop", 2, 1), ("form.pop_verse_chorus", 2, 2), ("form.loop_blocks", 0, 1),
                                                ("form.journey", 1, 2), ("form.mid8_ramp", 1, 2)])   # the song's own solo is one break; a bridge adds one
def test_form_options_shape_the_arrangement(oid, builds, breaks):
    pack = variety.apply_overrides(stylepack.load("house"), variety.overrides({"choices": {"form": oid}}, BANK))
    parts, toks = _form_parts()
    arr = songform.arrange(pack, parts, toks, origin_s=27.3085, bar_s=240.0 / 108.478)
    kinds = [s["name"] for s in arr["sections"]]
    assert kinds.count("build") == builds and kinds.count("break") == breaks, kinds
    tail = int(pack["form"].get("tail_bars", 8))
    assert bool(arr["slots"]["tail"]) == bool(tail) and all(z - a == tail for a, z in arr["slots"]["tail"])   # chop games after a chorus, or none
    if pack["form"].get("labels"):
        assert any(s.get("label") for s in arr["sections"])
        assert remixbuild.marker_names(arr["sections"])[0].startswith("Intro")


def test_new_bass_characters_voicings_and_arp_shapes():
    secs = [{"name": "drop", "start": 0, "end": 2}]
    pack = {"bass": {"drop": "x.v.7.4.b.d.3.o."}}
    keys = [n[2] for n in stylepack.line_notes(pack, "bass", secs, lambda b: 0, lambda pc, up: 48 + pc + 12 * up, lambda pc: 3)][:8]
    assert keys == [48, 43, 58, 53, 49, 36, 51, 60]
    assert stylepack.voice([60, 63, 67], "seventh") == [60, 63, 67, 70] and stylepack.voice([60, 64, 67], "seventh") == [60, 64, 67, 71]
    assert stylepack.voice([60, 64, 67], "seventh", dominant=True)[-1] == 70 and stylepack.voice([60, 63, 67], "minmaj")[-1] == 71
    ck = lambda pc, base=60: [base + pc, base + pc + 3, base + pc + 7]  # noqa: E731
    for shape in stylepack.ARP_SHAPES:
        spec = {"shape": shape, "rate": 16, "sections": ["drop"], "cell": [0, 3, 7, 12]}
        notes = stylepack.arp_notes({"arp": spec}, secs, lambda b: 9, ck, 9, "minor")
        assert notes and all(n[2] >= 60 for n in notes), shape
    fall = stylepack.arp_notes({"arp": {"shape": "fall", "rate": 16, "sections": ["drop"]}}, secs, lambda b: 0, ck)
    assert [n[2] for n in fall[:3]] == [79, 75, 72]                                    # top down
    trip = stylepack.arp_notes({"arp": {"shape": "rise", "rate": 12, "sections": ["drop"]}}, secs, lambda b: 0, ck)
    assert abs(trip[1][0] - trip[0][0] - 1 / 3) < 1e-9                                 # triplet 8ths
    seq = stylepack.arp_notes({"arp": {"shape": "sequence", "rate": 16, "sections": ["drop"], "cell": [1, 4, 6]}}, secs, lambda b: 0, ck, 0, "major")
    assert all((n[2] % 12) in stylepack.SCALES["major"] for n in seq)                  # the cell snaps to the key's scale


def test_forms_gap_and_drum_dropouts():
    pack = dict(stylepack.load("house"), form={"gap_before_drop": "beat", "drum_dropout_every": 2})
    secs = [{"name": "build", "start": 0, "end": 4}, {"name": "drop", "start": 4, "end": 8}, {"name": "groove", "start": 8, "end": 12}]
    plan = stylepack.drums(pack, secs)
    assert not [e for e in plan.events if e[0] == 3 and e[1] >= 12]                   # the build's last beat is empty
    assert not [e for e in plan.events if 8 <= e[0] < 12 and e[2] == "kick"]           # the second groove-or-drop block drops the kick


def _draft(seed, history=None, style="house"):
    words = json.load(open(DATA + "friends_vocal_words.json"))
    return songanalysis.draft_plan("friends_" + style, songanalysis.tokens(words["words"]), source_bpm=108.478, key_pc=9, origin_s=27.3085,
                                   title="friends in low places", style=style, variety={"seed": seed, "history": history or []}, mode="major")


def test_a_varied_plan_validates_differs_by_seed_and_builds(tmp_path):
    a, b = _draft("one"), _draft("two", history=[{"choices": _draft("one")["variety"]["choices"]}])
    for p in (a, b):
        assert songplan.validate(p) == [] and p["variety"]["choices"] and p["style_overrides"] and any("variety" in n for n in p["notes"])
    assert a["variety"]["choices"] != b["variety"]["choices"]
    assert a["sections"] != b["sections"] or a["style_overrides"] != b["style_overrides"]
    for plan in (a, b):
        songplan.apply(plan)
        try:
            work = tmp_path / plan["variety"]["seed"]
            (work / "sandbox").mkdir(parents=True)
            inp = remix_inputs(work, remixplan.CHOPS, remixplan.ECHOED)
            out = str(work / "sandbox" / "v.flp")
            rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], out, log=lambda *x: None)
            f = flpfile.Flp.load(out)
            assert rep["pattern_counts"]["Drums"] > 0 and f.tempo() == plan["bpm"]
            used = {e[2] for e in remixplan.drums().events}
            assert ("perc" in rep["channel_ids"]) == ("perc" in used) and ("ride" in rep["channel_ids"]) == ("ride" in used)
            if plan.get("kit"):
                samples = {f.channel_info(c)["sample"] for c in f.channel_ids()}
                assert set(plan["kit"].values()) & samples
        finally:
            songplan.apply(songplan.load("plans/friends_in_low_places.json"))


def test_a_demo_instrument_is_imported_in_its_register(tmp_path):
    """A plan instrument (a demo song's channel) becomes the part's channel, with its notes moved to the instrument's register."""
    (tmp_path / "sandbox").mkdir()
    plan = _draft("inst")
    songplan.apply(plan)
    inp = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
    plan["instruments"] = {"stab": {"label": "Demo Pluck", "register": ["C5", "C6"], "import": {"flp": "x", "channels": [1], "path": inp["sytrus"]}}}
    songplan.apply(plan)
    try:
        if not remixplan.stab_notes():
            pytest.skip("this draft's chords option plays no stab")
        out = str(tmp_path / "sandbox" / "i.flp")
        rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], out, log=lambda *x: None)
        assert rep["imported"]["stab"]["label"] == "Demo Pluck"
        f = flpfile.Flp.load(out)
        ch = rep["channel_ids"]["stab"]
        assert f.channel_info(ch)["name"] == "Stab - Demo Pluck"          # its own name says pluck (an arp): the part word keeps it a stab
        keys = [n[2] for notes in f.pattern_notes().values() for n in notes if n[1] == ch]
        assert keys and 72 - 12 <= sorted(keys)[len(keys) // 2] <= 84 + 12
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))


NEW_PACKS = ["afro_house", "afrobeats", "reggaeton", "trance", "melodic_techno", "liquid_dnb", "future_bass", "uk_drill", "lofi", "trip_hop",
             "pop_dance", "future_house", "big_room", "electro_industrial", "cinematic"]


@pytest.mark.parametrize("style", NEW_PACKS)
def test_the_demo_study_packs_plan_and_build(style, tmp_path):
    """Each pack the demo study added drafts a valid plan from the first song, as written (variety off) and with variety, and builds."""
    for var in (False, {"seed": style}):
        words = json.load(open(DATA + "friends_vocal_words.json"))
        plan = songanalysis.draft_plan("friends_" + style, songanalysis.tokens(words["words"]), source_bpm=108.478, key_pc=9, origin_s=27.3085,
                                       title="friends in low places", style=style, variety=var)
        assert songplan.validate(plan) == [], (style, var, songplan.validate(plan))
        pack = stylepack.load(style)
        assert any(src.startswith("FL Studio 2026 demo project") for src in pack["sources"])
        songplan.apply(plan)
        try:
            work = tmp_path / ("v" if var else "p")
            (work / "sandbox").mkdir(parents=True)
            inp = remix_inputs(work, remixplan.CHOPS, remixplan.ECHOED)
            rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], str(work / "sandbox" / "b.flp"), log=lambda *x: None)
            assert rep["pattern_counts"]["Drums"] > 0 and rep["markers"]
        finally:
            songplan.apply(songplan.load("plans/friends_in_low_places.json"))


def test_a_reharmonization_replaces_the_record_chords_with_two_chords_a_bar():
    """The Freejak study's loop (2026-10-28): iii then IV, ii then V, each change on step 8 (a 16th ahead of beat 3), under the whole song;
    the bass follows it inside the bar, and a minor song takes it from its relative major."""
    res = {"choices": {"harmony": "harmony.iii_IV_ii_V_pushed"}}
    assert variety.reharmonizes(res)
    roots, qual = variety.harmony_loop(res, 3, mode="major")                    # E flat major
    assert roots[:2] == [7, 5] and qual[7] == "min" and qual[8] == "maj7" and qual[10] == "six"
    assert variety.harmony_splits(res, 3, mode="major")[:2] == [[7, 8], [7, 10]]
    assert variety.harmony_loop(res, 0, mode="minor")[0][:2] == [7, 5]           # C minor: from E flat, its relative major
    old = (remixplan.ROOTS8, remixplan.BAR_ROOTS, remixplan.BAR_SPLITS)
    try:
        remixplan.ROOTS8, remixplan.BAR_ROOTS = tuple(roots), ()
        remixplan.BAR_SPLITS = tuple(tuple(x) for x in variety.harmony_splits(res, 3, mode="major"))
        assert [remixplan.root_pc(4, s) for s in (0, 6, 7, 15)] == [7, 7, 8, 8]
        pack = variety.apply_overrides(stylepack.load("house"), variety.overrides({"choices": {"bass": "bass.dotted_pump"}}))
        notes = stylepack.line_notes(pack, "bass", [{"name": "groove", "start": 4, "end": 6}], remixplan.root_pc, lambda pc, up: 36 + pc)
        bar4 = sorted((round(st * 4 - 64), k) for st, _d, k, _v in notes if 16 <= st < 20)   # beats: bar 4 starts on beat 16
        assert bar4 == [(0, 43), (4, 43), (7, 44), (10, 44), (13, 44)]           # G G then A flat from step 8 on
    finally:
        remixplan.ROOTS8, remixplan.BAR_ROOTS, remixplan.BAR_SPLITS = old


def test_the_whole_song_form_plays_at_the_style_standard_tempo():
    house = variety.apply_overrides(stylepack.load("house"), variety.overrides({"choices": {"form": "form.whole_song_turned"}}))
    assert house["form"]["tempo"] == "standard" and stylepack.standard_tempo(house, 100.0) == 124.0
    assert stylepack.pick_tempo(house, 100.0) == 118.0                         # the least speed-up, where the form asks for the standard
    assert stylepack.standard_tempo(house, 80.0) is None                       # x1.55 would rush the voice


FREEJAK = {"form": "form.whole_song_turned", "drums": "drums.house_layer_in", "bass": "bass.dotted_pump", "harmony": "harmony.iii_IV_ii_V_pushed",
           "fx": "fx.stop_bar_sweep", "vocal": "vocal.whole_in_order", "mix": "mix.mono_low_hard_pump"}


def test_the_freejak_recipe_drafts_validates_and_builds(tmp_path):
    """Every choice the Sorry study added, locked together: the plan turns the passes, plays at house's standard tempo, re-harmonizes with
    two chords a bar, and builds."""
    words = json.load(open(DATA + "friends_vocal_words.json"))
    plan = songanalysis.draft_plan("friends_freejak", songanalysis.tokens(words["words"]), source_bpm=108.478, key_pc=9, origin_s=27.3085,
                                   title="friends in low places", style="house", roots=[9] * 200, mode="major",
                                   variety={"seed": "fj", "lock": FREEJAK, "surprise": False})
    assert songplan.validate(plan) == []
    assert plan["bpm"] == 124.0 and plan["variety"]["choices"]["harmony"] == FREEJAK["harmony"]
    assert "bar_roots" not in plan and plan["bar_splits8"][0] == [7, 2] and any("re-harmonized" in n for n in plan["notes"])
    names = [s["name"] for s in plan["sections"]]
    assert "build" not in names and names[:4] == ["intro", "groove", "break", "drop"]
    vocal = [c[4] for c in plan["vocal_clips"] if (c[6] if len(c) > 6 else "vocals") == "vocals"]
    assert vocal[:2] == ["Verse 1", "Chorus 1 (break)"]
    songplan.apply(plan)
    try:
        (tmp_path / "sandbox").mkdir()
        inp = remix_inputs(tmp_path, remixplan.CHOPS, remixplan.ECHOED)
        out = str(tmp_path / "sandbox" / "fj.flp")
        rep = remixbuild.build(inp["base"], inp["sytrus"], inp["audio"], out, log=lambda *x: None)
        assert rep["pattern_counts"]["Drums"] > 0 and flpfile.Flp.load(out).tempo() == 124.0
        brk = next(s for s in plan["sections"] if s["name"] == "break")
        assert remixplan.reese_notes() and not [n for n in remixplan.reese_notes() if brk["start"] * 4 <= n[0] < brk["end"] * 4]   # out in breaks
    finally:
        songplan.apply(songplan.load("plans/friends_in_low_places.json"))
