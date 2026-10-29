"""The song's own form from its vocal and the remix arrangement that keeps it (src/coproducer/songform.py): checked on the first song, whose
form the research step confirmed (guitar intro, verse, chorus, guitar and pedal steel solo, verse, chorus, repeated choruses)."""
import json

from coproducer import songanalysis, songform, stylepack

DATA = "tests/data/"


def _song():
    toks = songanalysis.tokens(json.load(open(DATA + "friends_vocal_words.json"))["words"])
    act = json.load(open(DATA + "friends_vocal_activity.json"))
    return toks, act


def test_form_matches_the_song():
    toks, act = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478, activity=act)
    assert [(p["kind"], p["bar0"], p["bar1"]) for p in parts[:6]] == [
        ("intro", -12, -8), ("verse", -8, 8), ("chorus", 8, 24), ("instrumental", 24, 32), ("verse", 32, 48), ("chorus", 48, 64)]
    assert all(p["kind"] == "chorus" for p in parts[6:])                       # the ending repeats the chorus


def test_without_audio_whisper_gaps_are_not_trusted_for_breaks():
    toks, _ = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478)
    assert parts[1]["kind"] == "verse" and parts[2]["kind"] == "chorus" and parts[2]["bar0"] == 8   # the opening is still found


def test_arrangement_keeps_whole_verses_and_choruses_in_order():
    toks, act = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478, activity=act)
    arr = songform.arrange(stylepack.load("techno"), parts, toks)
    names = [s["name"] for s in arr["sections"]]
    assert names == ["intro", "groove", "build", "drop", "break", "groove", "build", "drop", "outro"]
    vocal = [c for c in arr["clips"] if c[6] == "vocals"]
    assert [(c[4], c[1]) for c in vocal] == [("Verse 1", -8), ("Chorus 1", 8), ("Verse 2", 32), ("Chorus 2", 48)]
    other = [c[4] for c in arr["clips"] if c[6] == "other"]
    assert other == ["Original intro", "Original verse 1", "Original solo"]   # the original's instruments, never under a synth copy of them
    drop = next(s for s in arr["sections"] if s["name"] == "drop")
    assert drop["end"] - drop["start"] == 24 and arr["slots"]["tail"][0] == (drop["start"] + 16, drop["end"])   # whole chorus, then the games
    assert arr["src_bar"][drop["start"]] == 8 and arr["src_bar"][drop["start"] + 16] == 8   # the tail replays the chorus chords


def test_chops_are_whole_phrases_and_games_never_overlap():
    toks, act = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478, activity=act)
    chorus = next(p for p in parts if p["kind"] == "chorus")
    chops = songform.phrase_chops(toks, chorus, "friends in low places")
    words = chops["hook"]["words"].split()
    assert words[0] == "cause" and "places" in words and words[-1] == "away"   # the couplet: the title line and the line sung after it
    assert chops["hook"]["after_pickup"] == 44.68                             # "'cause" is a pickup: left off when it is slurred in
    assert chops["stutter"]["words"] == "friends" and chops["stutter"]["end_mode"] == "word"   # one title syllable for the roll
    assert not any("whiskey" in v["words"] for k, v in chops.items() if k.startswith("line"))  # no line repeats the hook
    for name, spec in chops.items():
        assert (len(spec["words"].split()) >= 3 or name == "stutter") and spec["end_mode"] in ("word", "phrase")
        if spec["end_mode"] == "word":
            assert spec["end"] == spec["next_t0"]                              # the cut stops at the next word, not inside this one
    arr = songform.arrange(stylepack.load("techno"), parts, toks)
    lengths = {n: (v["end"] - v["start"]) / 1.161 / (240 / 126) for n, v in chops.items()}
    rows = songform.chop_games(arr["slots"], chops, lambda n: lengths[n])
    assert all(r[2] != "stutter" for r in rows)
    for (b0, s0, n0, *_), (b1, *_r) in zip(rows, rows[1:]):
        assert b0 + s0 / 16 + lengths[n0] <= b1 + 0.3, (b0, n0, b1)            # one phrase ends before the next (a last-bar answer may meet the hook's tail)
    assert [0, 4, "hook", 80, 60] in rows and any(r[0] == 39 and r[2] == "line1" for r in rows)   # where the person put them on Friends


def test_roots_and_scale_filter():
    assert songform.scale_roots(["A", "A#", "B", None, "G#"], 9) == [9, 9, 11, 11, 8]
    roots = songform.bar_roots([None, 0, 1, 9], [None, 4, 9] + [7] * 8, -1, 9)
    assert roots == [None, 4, 9, 9]                                            # G is not in A major: the A before it holds


def test_keys_notes_play_the_files_chords_cleanly():
    secs = [{"name": "intro", "start": 0, "end": 2}, {"name": "drop", "start": 2, "end": 4}]
    rows = songform.keys_notes(secs, [None, None, 9, 11], {9: "maj", 11: "min"}, "X.......x.......", 9)
    assert {r[0] for r in rows} == {8.0, 10.0, 12.0, 14.0}                     # the strum on the drop's two bars only
    bar2 = sorted(r[2] for r in rows if r[0] == 8.0)
    bar3 = sorted(r[2] for r in rows if r[0] == 12.0)
    assert bar2 == [57, 61, 64] and bar3 == [59, 62, 66]                       # A major and B minor, three notes, A3 to A4


def test_whisper_window_overlaps_are_merged():
    """Whisper's overlapping windows wrote some words twice (the test file jumps back from 149.98 s to 140 s and from 228.38 s to 220 s)."""
    words = json.load(open("tests/data/friends_vocal_words.json"))["words"]
    toks = songanalysis.tokens(words)
    assert all(b["t0"] >= a["t0"] for a, b in zip(toks, toks[1:]))
    assert not [a["w"] for a, b in zip(toks, toks[1:]) if a["w"] == b["w"] and b["t0"] < a["t1"] + 0.3]   # no word sung twice at once
    dup = [{"word": w, "start": a, "end": b} for w, a, b in (("well", 61.58, 62.34), ("i'm", 62.34, 62.86), ("i'm", 62.18, 62.86),
                                                             ("grace", 65.18, 66.02), ("graces", 65.14, 66.26), ("na", 70.0, 70.3), ("na", 70.3, 70.6))]
    assert [t["w"] for t in songanalysis.tokens(dup)] == ["well", "i'm", "graces", "na", "na"]


def test_the_last_build_carries_the_verse_on_and_ends_on_the_roll():
    """The person's edit of the techno remix (2026-10-26): verse 2 sung on over the last build, a stutter in its last bar, the drop restarts the chorus."""
    toks, act = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478, activity=act)
    arr = songform.arrange(stylepack.load("techno"), parts, toks, origin_s=27.3085, bar_s=240 / 108.478)
    v2 = next(c for c in arr["clips"] if c[4].startswith("Verse 2"))
    builds = [x for x in arr["sections"] if x["name"] == "build"]
    assert v2[4] == "Verse 2 into the chorus" and v2[3] > 132.9 + 10           # it runs on well into the chorus
    assert v2[3] <= 27.3085 + (32 + builds[1]["end"] - 1 - v2[0]) * 240 / 108.478   # and ends before the build's last bar
    assert arr["slots"]["stutter"] == [builds[1]["end"] - 1] and arr["slots"]["build"] == [(builds[0]["start"], builds[0]["end"])]


def test_every_part_keeps_every_chorus_back_to_back_without_builds():
    toks, act = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478, activity=act)
    arr = songform.arrange(stylepack.load("house"), parts, toks, verses=None, choruses=None)
    names = [s["name"] for s in arr["sections"]]
    assert names == ["intro", "groove", "build", "drop", "break", "groove", "build", "drop", "drop", "drop", "drop", "outro"]
    vocal = [c[4] for c in arr["clips"] if c[6] == "vocals"]
    assert vocal == ["Verse 1", "Chorus 1", "Verse 2", "Chorus 2", "Chorus 3", "Chorus 4", "Chorus 5"]
    assert len(arr["slots"]["tail"]) == 2                                     # games only after a chorus that is not followed by another


def _sung(lines_at):
    """Word records from (start, text) lines, one word every 0.3 s."""
    out = []
    for t, text in lines_at:
        for k, w in enumerate(text.split()):
            out.append({"w": w, "t0": t + 0.3 * k, "t1": t + 0.3 * k + 0.28})
    return out


def test_form_by_repeats_when_the_title_opens_no_chorus():
    """The Curse of Curves sings its title only at the end of a section: what the song sings again is the chorus (2026-10-26)."""
    verse1 = [(0.0, "walking down a street of broken glass tonight"), (4.0, "nobody knows the name i gave away")]
    chorus = [(8.0, "the silver river runs beneath the city lights"), (12.0, "and every window sings along with me")]
    verse2 = [(16.0, "summer falls asleep inside a paper cup"), (20.0, "counting every penny that you never spent")]
    chorus2 = [(t + 16.0, s) for t, s in chorus]
    toks = _sung(verse1 + chorus + [(t + 8.0, s) for t, s in verse2] + [(t + 8.0, s) for t, s in chorus2])
    act = [(0.0, 40.0)]
    bar_s = 1.0
    parts = songform.form_by_repeats(toks, 0.0, bar_s, activity=act)
    assert [p["kind"] for p in parts] == ["verse", "chorus", "verse", "chorus"]
    assert [p["bar0"] for p in parts] == [0, 8, 24, 32]
    assert songform.form(toks, "the curse of curves", 0.0, bar_s, activity=act)[0]["kind"] == "verse"   # the title finds nothing here
    assert songform.repeated_words(toks)[toks.index(next(t for t in toks if t["w"] == "silver"))]


def test_harmony_roots_read_the_chords_when_there_is_no_bass():
    """"Girls" has no bass line: the roots come from the harmony stem, F and D minor alternating bar by bar."""
    import numpy as np
    rate, bar_s = 22050, 2.0
    t = np.arange(int(rate * bar_s)) / rate

    def chord(*midi):
        return sum(np.sin(2 * np.pi * 440 * 2 ** ((n - 69) / 12) * t) for n in midi)
    x = np.concatenate([chord(65, 69, 72) if b % 2 == 0 else chord(62, 65, 69) for b in range(6)]).astype("float32")
    assert songform.harmony_roots(x, rate, 0.0, bar_s, 0, 6, 5) == ["F", "D", "F", "D", "F", "D"]


def test_a_one_word_title_marks_the_lines_it_ends():
    toks = _sung([(0.0, "walking down the street tonight"), (3.0, "all i really want is girls"), (6.0, "in the morning it is girls"),
                  (9.0, "in the evening it is girls"), (12.0, "nobody knows the name i gave")])
    marks = songform.title_lines(toks, "girls")
    assert not marks[0] and all(marks[5:20]) and not marks[-1]
    assert not any(songform.title_lines(toks, "the curse of curves"))   # only a one-word title


def test_a_form_turns_each_pass_into_a_different_function():
    """Freejak's Sorry remix (2026-10-28): verse 1 on the groove, chorus 1 sung in a break and then a drop of hook games, verse 2 in a
    break, chorus 2 on the drop, a short break before the last hook drop; no builds, an empty bar before every drop."""
    toks, act = _song()
    parts = songform.form(toks, "friends in low places", 27.3085, 240 / 108.478, activity=act)
    pack = stylepack.load("house")
    pack["form"] = {"build": "never", "verse_as": ["groove", "break"], "chorus_as": ["break", "drop"], "drop_after": 16, "tail_bars": 16,
                    "tail_break": 2, "gap_before_drop": "bar"}
    arr = songform.arrange(pack, parts, toks)
    names = [s["name"] for s in arr["sections"]]
    assert names[:8] == ["intro", "groove", "break", "drop", "break", "break", "drop", "break"] and names[-2:] == ["drop", "outro"]
    vocal = [(c[4], c[0]) for c in arr["clips"] if c[6] == "vocals"]
    secs = arr["sections"]
    assert vocal[1] == ("Chorus 1 (break)", secs[2]["start"]) and vocal[2] == ("Verse 2", secs[5]["start"])
    assert secs[3]["end"] - secs[3]["start"] == 16 and arr["slots"]["tail"][0] == (secs[3]["start"], secs[3]["end"])   # the hook drop
    assert "build" not in names
    short = [s for s in secs if s["name"] == "break" and s["end"] - s["start"] == 2]
    assert len(short) == 1 and arr["slots"]["tail"][-1][0] == short[0]["end"]          # the breath, then the last hook drop
    plan = stylepack.drums(pack, secs)
    first_drop = secs[3]["start"]
    assert not [e for e in plan.events if e[0] == first_drop - 1]                     # the stop bar before the drop is empty
