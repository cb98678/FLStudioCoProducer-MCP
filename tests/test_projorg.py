import struct
from pathlib import Path

from coproducer import flporg, flpfile, projorg
from coproducer.testflp import project, with_organization

DOC = Path(__file__).resolve().parent.parent / "docs" / "PROJECT_STANDARD.md"


def test_tidy_names():
    assert projorg.tidy("CP_Chop_hook_2") == "Chop Hook 2"
    assert projorg.tidy("909 CH 2") == "Hat Closed" and projorg.tidy("707 OH") == "Hat Open"
    assert projorg.tidy("Vocal 124 bpm") == "Vocal 124 BPM" and projorg.tidy("FX bed") == "FX Bed"
    assert projorg.tidy("Chop hook #2") == "Chop Hook 2"
    assert projorg.tidy(projorg.tidy("Chop hook_echo")) == projorg.tidy("Chop hook_echo")  # idempotent


def test_families_and_group_words():
    assert projorg.family_of("Kick") == "drums" and projorg.family_of("Drums 1") == "drums"
    assert projorg.family_of("Reese Bass") == "bass" and projorg.family_of("Rising Arp") == "synths"
    assert projorg.family_of("Chop hook") == "vocals" and projorg.family_of("FX bed") == "fx"
    assert projorg.family_of("Mystery") is None


def test_palette_is_distinct_and_documented():
    assert len(set(projorg.PALETTE.values())) == len(projorg.PALETTE)
    text = DOC.read_text(encoding="utf-8")
    for fam, (r, g, b) in projorg.PALETTE.items():
        assert "#%02X%02X%02X" % (r, g, b) in text, fam


def test_names_are_made_unique():
    f = with_organization(project({0: "Chop hook", 1: "Chop_hook", 2: "Kick"}, {}))
    assert [r["new"] for r in projorg.plan_channels(f)] == ["Chop Hook", "Chop Hook 2", "Kick"]


def test_apply_is_idempotent_and_roundtrips(tmp_path):
    f = with_organization(project({0: "Kick", 1: "Chord Stab"}, {0: [0]}))
    f.set_track(0, 1)
    f.set_track(1, 2)
    projorg.apply(f, projorg.plan(f))
    once = f.to_bytes()
    assert projorg.check(f) == []
    projorg.apply(f, projorg.plan(f))
    assert f.to_bytes() == once
    path = tmp_path / "x.flp"
    path.write_bytes(once)
    assert projorg.check(flpfile.Flp.load(str(path))) == []
    assert flporg.display_groups(flpfile.Flp.load(str(path))) == ["Audio", "Drums", "Synths", "Unsorted"]


def test_a_project_without_organization_events_is_skipped_not_broken():
    f = project({0: "Kick"}, {0: [0]})
    f.set_track(0, 1)
    counts = projorg.apply(f, projorg.plan(f))
    assert counts["skipped"] > 0


def test_a_colour_switches_the_inserts_appearance_flag_on():
    """FL ignores an insert colour unless event 42 is 1 (found on a live project: inserts without it stayed grey)."""
    f = with_organization(project({0: "Kick"}, {0: [0]}))
    f.set_track(0, 1)
    flag = lambda: next(v for e, v in f.events[slice(*flporg.insert_range(f, 1))] if e == flporg.EV_INS_FLAGS)  # noqa: E731
    assert flag() == b"\x00"
    flporg.set_insert(f, 1, name="Kick")
    assert flag() == b"\x00"  # a name alone does not need it
    projorg.apply(f, projorg.plan(f))
    assert flag() == b"\x01" and flporg.insert_color(f, 1) == projorg.PALETTE["drums"]


def _organized_with_rows():
    f = with_organization(project({0: "Kick", 1: "Chord Stab", 2: "Chop Hook"}, {0: [0], 1: [0], 2: [0]}))
    for c in range(3):
        f.set_track(c, c + 1)
    f.add_pattern(2, "Drums 1", b"")
    f.add_playlist_clips([(2, 0, 2, 2)])
    return f


def test_channels_show_the_right_colour_and_group_the_way_fl_loads_them():
    """FL sorts group names but keeps the stored indices, and ignores a colour while the appearance flag is 0. Both showed up in a file FL saved."""
    f = with_organization(project({0: "Kick", 1: "Chord Stab", 2: "Chop Hook", 3: "Mystery"}, {0: [0]}))
    assert flporg.display_groups(f) == ["Audio", "Unsorted"] and flporg.shown_channel_color(f, 0) == flporg.DEFAULT_CH_COLOR  # flag 0: grey
    projorg.apply(f, projorg.plan(f))
    names = flporg.display_groups(f)
    assert names == sorted(names, key=str.lower)  # written the way FL keeps them
    assert [flporg.shown_group(f, c) for c in range(3)] == ["Drums", "Synths", "Vocals"]
    assert [flporg.shown_channel_color(f, c) for c in range(3)] == [projorg.PALETTE[x] for x in ("drums", "synths", "vocals")]
    assert flporg.shown_group(f, 3) == "Audio"  # a channel the standard leaves alone keeps its group when the list is re-sorted
    assert projorg.check(f) == []


def test_check_catches_what_fl_would_show_wrong():
    f = with_organization(project({0: "Kick"}, {0: [0]}))
    f.set_track(0, 1)
    projorg.apply(f, projorg.plan(f))
    f.events[f._find(0, flporg.EV_CH_FLAG)][1] = b"\x00"  # colour written but not switched on
    assert any("colour" in p for p in projorg.check(f))
    f.events[f._find(0, flporg.EV_CH_FLAG)][1] = b"\x01"
    k = f._find(0, flporg.EV_CH_GROUP)
    f.events[k][1] = struct.pack("<i", 0)  # an index that points at the wrong name once sorted
    assert any("group" in p for p in projorg.check(f))


def test_playlist_rows_and_insert_colours_need_their_flags():
    f = _organized_with_rows()
    projorg.apply(f, projorg.plan(f))
    for r in projorg.plan_rows(f):
        assert flporg.shown_row_color(f, r["index"]) == r["color"]
    assert flporg.shown_insert_color(f, 1) == projorg.PALETTE["drums"]
    f.events[flporg._track_at(f, projorg.plan_rows(f)[0]["index"]) + 1][1] = b"\x00"
    assert any("playlist row" in p and "colour" in p for p in projorg.check(f))


def test_automation_clips_get_their_group_and_a_row_block_below_the_music():
    from coproducer import automation
    f = with_organization(project({0: "Kick", 1: "Chord Stab"}, {0: [0]}), rows=8)
    f.set_track(0, 1)
    f.set_track(1, 2)
    automation.add_automation_clip(f, 2, "Filter Sweep Drop", automation.mixer_link(2), [(0, 0.0), (4, 1.0)], start_beat=16, track=0)
    automation.add_automation_clip(f, 3, "Pump Kick", automation.mixer_link(1), [(0, 0.8), (1, 0.2)], start_beat=0, track=0)
    p = projorg.plan(f)
    assert [(r["channel"], r["name"], r["rows"], r["index"]) for r in p["automation_rows"]] == [(3, "Pump Kick", [0], 3), (2, "Filter Sweep Drop", [0], 4)]
    assert [r["family"] for r in p["channels"]] == ["drums", "synths", "automation", "automation"]  # a clip named Kick is not a drum
    assert all(r["index"] != 1 for r in p["rows"])  # row 1 held only automation, so the family rows leave it alone
    assert any("automation block" in x for x in projorg.check(f))
    projorg.apply(f, p)
    assert projorg.check(f) == []
    rows = {struct.unpack("<H", it[6:8])[0]: 499 - struct.unpack("<H", it[12:14])[0] for it in f.playlist_items()}
    assert rows[3] == 2 and rows[2] == 3
    assert flporg.track_name(f, 3) == "Pump Kick" and flporg.shown_row_color(f, 4) == projorg.AUTOMATION_COLOR
    assert flporg.shown_group(f, 2) == "Automation" and flporg.shown_channel_color(f, 3) == projorg.AUTOMATION_COLOR
