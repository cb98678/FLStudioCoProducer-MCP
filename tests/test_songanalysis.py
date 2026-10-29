"""Song analysis on the first song: the planner has to find what was picked by hand, and the downbeat has to match the bar line the build uses."""
import json
from pathlib import Path

import pytest

from coproducer import arrange, remixplan, songanalysis as sa, songplan

DATA = Path(__file__).parent / "data"
TITLE = "Friends in Low Places"


@pytest.fixture(scope="module")
def toks():
    return sa.tokens(json.loads((DATA / "friends_vocal_words.json").read_text())["words"])


@pytest.fixture
def restore():
    saved = songplan.export_current()
    yield
    songplan.apply(saved)


def test_tokens_drop_words_with_no_time():
    t = sa.tokens([{"word": "Hello,", "start": 1.0, "end": 1.4}, {"word": "ghost", "start": 2.0, "end": 2.0}, {"word": "...", "start": 3.0, "end": 3.5}])
    assert [x["w"] for x in t] == ["hello"]


def test_lines_that_differ_in_little_words_count_together():
    words = [(w, i * 0.4, i * 0.4 + 0.35) for i, w in enumerate("got friends in the low places so friends in low places".split())]
    t = sa.tokens([{"word": w, "start": a, "end": b} for w, a, b in words])
    rep = sa.repeated_spans(t)
    assert ("friends", "low", "places") in rep and len(rep[("friends", "low", "places")]) == 2


def test_downbeat_matches_the_bar_line_the_build_uses():
    h = json.loads((DATA / "friends_drum_hits.json").read_text())
    found = sa.find_downbeat(sa.hit_rows(h["hits"]), h["bpm"], h["offset_s"])
    bar = 240.0 / h["bpm"]
    off = (found["origin_s"] - h["origin_s"]) / bar
    assert abs(off - round(off)) * bar < 0.02, found    # within 20 ms of a bar line of the hand-set origin
    assert found["scores"][found["step"]] == max(found["scores"])


def test_downbeat_on_a_synthetic_backbeat_with_an_entrance():
    bpm, step = 120.0, 60.0 / 120.0 / 4
    hits = []
    for bar in range(8):
        base = 3.0 + bar * 16 * step                  # drums enter at 3.0 s on a bar line
        hits += [{"t": base, "kind": "kick", "s": 1.0}, {"t": base + 8 * step, "kind": "kick", "s": 1.0},
                 {"t": base + 4 * step, "kind": "snare", "s": 1.0}, {"t": base + 12 * step, "kind": "snare", "s": 1.0}]
    f = sa.find_downbeat(hits, bpm, 3.0 % step)
    assert abs(f["origin_s"] - 3.0) < 0.01


def test_chop_planner_finds_the_hand_picked_chops(toks):
    plan = sa.plan_chops(toks, title=TITLE)
    hook, hand = plan["chops"]["hook"], remixplan.CHOPS["hook"]
    assert abs(hook["start"] - hand["start"]) < 0.5 and abs(hook["end"] - hand["end"]) < 0.5, hook
    said = {c["words"] for c in plan["chops"].values()}
    for want in ("friends", "low places", "whiskey", "blues away", "okay"):
        assert want in said, (want, sorted(said))


def test_without_a_title_the_most_repeated_line_is_the_hook(toks):
    plan = sa.plan_chops(toks)
    assert len(plan["chops"]["hook"]["words"].split()) >= 3


def test_no_repeated_line_is_an_error():
    t = sa.tokens([{"word": w, "start": i * 0.5, "end": i * 0.5 + 0.4} for i, w in enumerate("every single word here is different today".split())])
    with pytest.raises(ValueError):
        sa.plan_chops(t)


def test_draft_plan_is_a_valid_plan_with_clips_near_the_hand_cut(toks, restore):
    plan = sa.draft_plan("draft", toks, source_bpm=108.478, key_pc=9, origin_s=27.3085, title=TITLE)
    assert songplan.validate(plan) == []
    chorus = plan["vocal_clips"][0]
    assert abs(chorus[2] - 132.9) < 0.5 and abs(chorus[3] - 148.2) < 1.0 and chorus[1] == 48
    assert plan["roles"]["closers"][0] == "okay" and arrange.missing_roles(plan["roles"]) == []
    songplan.apply(plan)                         # the recipe accepts it and places every chop inside the song
    ev = remixplan.chop_events()
    assert ev and max(e[0] for e in ev) < remixplan.TOTAL_BARS and {e[2] for e in ev} <= set(plan["chops"]) | {n + "_echo" for n in plan["echoed"]}
    assert "default" in " ".join(plan["notes"])


def test_loop_roots_takes_the_most_common_root_per_position():
    roots = [9, 9, 9, 9, 11, 11, 4, 4] * 3 + [None, 9, 9, 9, 5, 11, 4, 4]
    assert sa.loop_roots(roots) == [9, 9, 9, 9, 11, 11, 4, 4]
    with pytest.raises(ValueError):
        sa.loop_roots([None] * 8)


def test_sections_from_bars_splits_on_level_jumps_and_labels():
    db = [-30.0] * 4 + [-20.0] * 8 + [-14.0] * 8 + [-22.0] * 4
    secs = sa.sections_from_bars(db, vocal_bars=set(range(4, 12)), hook_bars=set(range(12, 20)))
    assert [(s["start"], s["end"], s["label"]) for s in secs] == [(0, 4, "intro"), (4, 12, "verse"), (12, 20, "chorus"), (20, 24, "outro")]


def test_loop_roots_accepts_note_names_and_starts_the_loop_on_the_tonic():
    names = ["B", "E", "E", "E", "E", "A", "A", "A"] * 3
    assert sa.loop_roots(names) == [11, 4, 4, 4, 4, 9, 9, 9]
    assert sa.loop_roots(names, tonic=9) == [9, 9, 9, 11, 4, 4, 4, 4]
