from coproducer import remixplan as R


def test_sections_are_contiguous_and_cover_the_song():
    prev = 0
    for s in R.SECTIONS:
        assert s["start"] == prev and s["end"] > s["start"]
        prev = s["end"]
    assert prev == R.TOTAL_BARS


def test_keys():
    assert R.sub_key(9) == 40  # A1 sounds as MIDI 33, the patch adds 7
    assert R.reese_key(9) == 60 and R.reese_key(11) == 62 and R.reese_key(4) == 55
    assert [k % 12 for k in R.chord_keys(4)] == [4, 8, 11]
    assert R.root_pc(0) == 9 and R.root_pc(4) == 11 and R.root_pc(6) == 4 and R.root_pc(8) == 9


def test_fader_raw():
    assert R.fader_raw(0.0) == 12800
    assert R.fader_raw(-6.0) < 12800 < R.fader_raw(3.0)


def test_drums_have_four_on_the_floor_in_drops_and_none_in_breaks():
    p = R.drums()
    kicks = {(b, s) for b, s, i, *_ in p.events if i == "kick"}
    for b in range(40, 56):
        assert all((b, s) in kicks for s in (0, 4, 8, 12))
    for b in range(24, 31):
        assert not any(k[0] == b for k in kicks)
    assert max(b for b, *_ in p.events) < R.TOTAL_BARS


def test_bass_never_overlaps_a_kick_and_stays_in_range():
    p = R.drums()
    ks = R.kick_beats(0, R.TOTAL_BARS, p)
    for st, d, key, vel in R.sub_notes(p):
        assert 0 <= st < R.TOTAL_BARS * 4 and 1 <= vel <= 127
        assert not any(st + 1e-6 < k < st + d for k in ks), (st, d)
    for notes in (R.reese_notes(), R.stab_notes(), R.arp_notes()):
        assert notes and all(0 <= n[0] < R.TOTAL_BARS * 4 and 1 <= n[3] <= 127 for n in notes)


def test_chops_and_clips_are_defined():
    names = {c[2] for c in R.chop_events()}
    assert names <= set(R.chop_names())
    assert all(0 <= c[0] < R.TOTAL_BARS and 0 <= c[1] < 16 and 1 <= c[3] <= 127 for c in R.chop_events())
    assert all(c["start"] < c["end"] and c["end_mode"] in ("word", "phrase") for c in R.CHOPS.values())
    assert set(R.ECHOED) <= set(R.CHOPS)
    for bar, _ob, a, b, _label, mode in R.VOCAL_CLIPS:
        assert mode in ("word", "phrase")
        assert 0 <= bar < R.TOTAL_BARS and a < b


def test_fx_cues_render_in_the_bed():
    from coproducer import fxbed
    x = fxbed.render_bed(R.fx_cues(), R.BPM, R.TOTAL_BARS * 4)
    assert x.shape[1] == 2 and abs(x).max() > 0.01


def test_reese_pluck_is_tuned_stereo_and_decays():
    import numpy as np

    from coproducer import oneshots
    x = oneshots.reese_pluck()
    assert x.ndim == 2 and x.shape[1] == 2 and 0.9 < np.abs(x).max() <= 1.0
    spec = np.abs(np.fft.rfft(x[:, 0]))
    assert abs(np.fft.rfftfreq(len(x), 1 / oneshots.SR)[int(np.argmax(spec))] - 55.0) < 3.0
    assert np.abs(x[-200:]).max() < 0.02


def _durations():
    dry = {n: 1.0 for n in R.CHOPS}
    dry.update({"hook": 3.4, "okay": 1.95, "drowns": 1.7, "bluesaway": 1.8})
    full = dict(dry)
    for n in R.ECHOED:
        dry[n + "_echo"] = dry[n]
        full[n + "_echo"] = dry[n] + 2.0
    return dry, full


def test_closing_okay_has_clear_air():
    ev = R.chop_events()
    for bar, name in ((54, "okay"), (94, "okay_echo")):  # first drop closes dry (the break's pick-up follows), the second with its echo
        assert [e[2] for e in ev if e[0] == bar] == [name]
    dry, full = _durations()
    bad = [c for c in R.chop_conflicts(ev, dry, full) if "okay" in c or "bar 54" in c or "bar 94" in c]
    assert bad == []
    # the dry hook before it ends before the okay starts
    bar_s = 240.0 / R.BPM
    assert 52 * bar_s + 2 * bar_s / 16 + dry["hook"] < 54 * bar_s


def test_gabber_chatter_is_gone_from_drop_two():
    names = {e[2] for e in R.chop_events() if 80 <= e[0] < 88}
    assert "friends" not in names and "blues" not in names


def test_chop_conflicts_flags_overlapping_dry_chops():
    ev = [(54, 0, "okay_echo", 100, 60), (54, 10, "drowns", 100, 60)]
    dry, full = _durations()
    assert any("drowns" in c and "dry part" in c for c in R.chop_conflicts(ev, dry, full))


def test_break_two_verse_plays_out_to_the_end_of_its_phrase():
    bar, orig_bar, a, b, label, mode = R.VOCAL_CLIPS[1]
    assert bar == 56 and b > 78.0 and mode == "phrase"  # the verse's last line, "low places", ends at 78.4 s and lands on the 64 marker
    assert R.CLIP_WORDS[1]["tail"] == "low places"


def test_teasers_and_pickups_clear_the_next_entry():
    ev = R.chop_events()
    dry, full = _durations()
    dry.update({"lowplaces": 1.91, "friends": 0.75, "friends_echo": 0.75})
    bar_s = 240.0 / R.BPM
    (b, st, *_), = [e for e in ev if e[2] == "lowplaces" and e[0] < 8]
    assert b * bar_s + st * bar_s / 16 + dry["lowplaces"] <= 8 * bar_s + 0.01  # the intro teaser ends before the groove's first hook
    (b, st, *_), = [e for e in ev if e[2] == "friends_echo" and e[0] == 23]
    pickup = 24 * bar_s - 0.3  # the break clip starts about 0.3 s early (its first words are a pick-up)
    assert b * bar_s + st * bar_s / 16 + dry["friends_echo"] <= pickup + 0.1


def test_diatonic_triads_follow_the_mode():
    keep = (R.DIATONIC, R.MODE, R.KEY_PC, dict(R.ROOT_QUALITY))
    try:
        R.DIATONIC, R.ROOT_QUALITY = True, {}
        R.MODE, R.KEY_PC = "minor", 9                                   # A minor: i, iv and v minor, III, VI and VII major
        assert [R.chord_third(pc) for pc in (9, 2, 4, 0, 5, 7)] == [3, 3, 3, 4, 4, 4]
        R.ROOT_QUALITY = {4: "maj", 2: "maj"}                           # a plan's root_quality still wins (E major, the Dorian D)
        assert R.chord_third(4) == 4 and R.chord_third(2) == 4 and R.chord_third(9) == 3
        R.MODE, R.KEY_PC, R.ROOT_QUALITY = "major", 9, {}               # A major as before: ii, iii and vi minor
        assert [R.chord_third(pc) for pc in (9, 11, 1, 6)] == [4, 3, 3, 3]
    finally:
        R.DIATONIC, R.MODE, R.KEY_PC = keep[0], keep[1], keep[2]
        R.ROOT_QUALITY = keep[3]
