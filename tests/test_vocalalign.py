"""The vocal slice rule (skill vocal-slice-align) on synthetic clips: phrases to the singer's grid, riffs by their first onset, throws with
their phrase, duplicates, flams and contiguous slices handled; and the FLP helpers it needs."""
from coproducer import flpfile as F
from coproducer import testflp, vocalalign as V

SRC, ORIGIN, PPQ = 86.0, 0.0755, 96
K = SRC / 60.0


def clip(pos_beats, start_s, end_s, mixer=10, ch=24, row=1):
    return V.Clip(ch, int(round(pos_beats * PPQ)), int(round((end_s - start_s) * K * PPQ)), start_s, end_s, row, mixer)


def test_a_phrase_lands_on_her_beats_and_her_chord_grid_with_her_lead():
    c = clip(63.3333, 0.0, 13.1246)          # Hello Toni's verse 1 as the person dragged it: her bar 0.44 beat late
    V.plan_moves([c], [], SRC, ORIGIN, PPQ, lead_s=0.025)
    assert c.kind == "phrase"
    her0 = c.new_pos / PPQ + 0.1082            # where her beat 0 lands (origin 0.0755 s = 0.1082 of her beats into the file)
    assert abs(her0 - (64.0 + 0.025 * K)) < 1.5 / PPQ   # bar 17, plus the lead, within a tick
    assert c.length == int(round(13.1246 * K * PPQ))


def test_a_short_phrase_matches_her_beats_only_and_a_riff_snaps_its_first_onset_to_a_16th():
    p = clip(83.8125, 13.2703, 15.9593)       # 3.85 beats: her beats on beats, parity free
    V.plan_moves([p], [], SRC, ORIGIN, PPQ, lead_s=0.0)
    d = p.new_pos / PPQ - V.her_beat(13.2703, SRC, ORIGIN)
    assert abs(d - round(d)) < 1.5 / PPQ and p.shift_beats > 0
    r = clip(99.0833, 41.9357, 42.5462)       # "Just": a riff with its onset at the cut
    V.plan_moves([r], [41.9415], SRC, ORIGIN, PPQ)
    assert r.kind == "riff" and abs(r.new_pos / PPQ + (41.9415 - 41.9357) * K - 99.0) < 1.0 / PPQ   # the onset on beat 99, the clip just before it


def test_duplicates_flams_and_contiguous_slices():
    a = clip(63.3333, 0.0, 5.9736)
    b = clip(63.3333 + 5.9736 * K + 0.05, 5.9736, 8.7762)    # the next slice, placed where the window continues (0.05 beat off)
    d = clip(83.8125, 13.27, 15.96, ch=29)                     # an identical copy on a clone channel
    d2 = clip(83.8125, 13.27, 15.96)
    fl = clip(350.5, 22.75, 24.494)                            # the tail of the long hook, sliced off while the copy still plays it
    hook = clip(336.0, 12.634, 24.494, ch=29)
    clips = V.dedupe([a, b, d2, d, fl, hook], PPQ, SRC)
    assert d.kind == "dup" and d2.kind == "" and fl.kind == "flam" and hook.kind == ""
    clips = V.merge_contiguous(clips, SRC, PPQ)
    assert b.kind == "merged" and a.end_s == 8.7762 and a.merged == [b.pos]


def test_a_throw_follows_its_phrase():
    p = clip(260.75, 28.6508, 36.215)
    t = clip(268.979, 34.392, 36.215, mixer=16, ch=30, row=2)
    V.plan_moves([p, t], [], SRC, ORIGIN, PPQ, lead_s=0.025)
    assert t.kind == "throw" and t.new_pos == int(round(p.new_pos + (34.392 - 28.6508) * K * PPQ))


def test_apply_rewrites_the_vocal_clips_on_one_channel_per_mixer_track():
    f = testflp.project({0: "Vocal", 1: "Vocal #2", 2: "Kick"}, {2: [0, 96]})
    tmpl = bytearray(88)
    f.add_audio_clips(0, 1, [(0, 96, 0.0, 697.7), (960, 96, 0.0, 697.7)], bytes(tmpl))
    f.add_audio_clips(1, 2, [(960, 96, 0.0, 697.7)], bytes(tmpl))
    clips = V.collect(f, {0: 0.0, 1: 0.0}, {0: 10, 1: 10})
    assert len(clips) == 3
    clips = V.dedupe(clips, PPQ, SRC)
    V.plan_moves(clips, [0.01], SRC, ORIGIN, PPQ)
    done = V.apply(f, clips, {10: 1}, {10: 0}, bytes(tmpl), {0, 1})
    assert done == {"removed": 3, "added": 2}
    assert sorted(a["channel"] for a in f.audio_clips()) == [0, 0]


def test_quantize_notes_moves_starts_to_the_grid_and_keeps_lengths():
    f = testflp.project({0: "Arp", 1: "Kick"}, {0: [5, 30, 70], 1: [0, 96]})
    moved = f.quantize_notes({0}, 24)
    notes = [n for p in f.pattern_notes().values() for n in p if n[1] == 0]
    assert moved == 3 and sorted(n[0] for n in notes) == [0, 24, 72]
    assert all(n[0] % 24 == 0 for p in f.pattern_notes().values() for n in p if n[1] == 1)


def test_set_track_name_names_a_playlist_row():
    import struct
    f = testflp.project({0: "Vocal"}, {0: [0]})
    at = next(i for i, (e, _v) in enumerate(f.events) if e == F.EV_PLAYLIST)
    f.events[at:at] = [[F.EV_TRACK, struct.pack("<I", 1) + bytes(60)], [43, b"\x00"], [F.EV_TRACK, struct.pack("<I", 2) + bytes(60)], [43, b"\x00"]]
    f.set_track_name(1, "Vocal FX")
    assert [e for e, _v in f.events[at:at + 6]] == [F.EV_TRACK, 43, F.EV_TRACK, 43, F.EV_TRACK_NAME, F.EV_PLAYLIST]
    names = [v.decode("utf-16-le").rstrip("\0") for e, v in f.events if e == F.EV_TRACK_NAME]
    assert "Vocal FX" in names
