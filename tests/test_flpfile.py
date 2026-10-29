import struct

import pytest

from coproducer import flpfile as F


def _playlist_item(pos, pid, length, track, item_id):
    it = bytearray(88)
    it[0:4] = struct.pack("<I", pos)
    it[6:8] = struct.pack("<H", F.PATTERN_BASE + pid)
    it[8:12] = struct.pack("<I", length)
    it[12:14] = struct.pack("<H", 499 - track)
    it[32:36] = struct.pack("<I", item_id)
    return bytes(it)


def synthetic(channels=(2, 3, 7)) -> bytes:
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, len(channels), 96)
    ev = [[199, F.enc16("26.1.7")], [65, struct.pack("<H", 1)], [193, F.enc16("Pat 1")], [224, F.note_bytes(0, 2, 60)]]
    for c in channels:
        ev += [[64, struct.pack("<H", c)], [0, b"\x01"], [203, F.enc16("Ch%d" % c)], [196, F.enc16("C:\\old%d.wav" % c)], [104, struct.pack("<H", 5)], [213, b"\x01\x02\x03"]]
    ev += [[99, b"\x00\x00"], [233, _playlist_item(0, 1, 384, 3, 1)]]
    return F.emit(head, ev, b"")


def test_round_trip_is_exact():
    data = synthetic()
    assert F.emit(*F.parse(data)) == data


def test_set_sample_name_enabled_and_track():
    f = F.Flp(*F.parse(synthetic()))
    f.set_sample(3, "C:\\kits\\snare.wav", "Snare")
    f.set_enabled(3, False)
    f.set_track(3, 9)
    g = F.Flp(*F.parse(f.to_bytes()))
    assert g.get_text(3, F.EV_SAMPLE_PATH) == "C:\\kits\\snare.wav" and g.get_text(3, F.EV_CH_NAME) == "Snare"
    assert g.get_text(2, F.EV_CH_NAME) == "Ch2"
    i, j = g.block(3)
    assert g.events[i + 1] == [0, b"\x00"] and g.events[g._find(3, F.EV_CH_TRACK)][1] == struct.pack("<H", 9)


def test_clone_channel_updates_count_and_refuses_duplicates():
    f = F.Flp(*F.parse(synthetic()))
    f.clone_channel(7, 160, "Remix Sub", track=45)
    assert f.channel_ids() == [2, 3, 7, 160] and f.channel_count == 4
    assert f.get_text(160, F.EV_CH_NAME) == "Remix Sub" and f.get_text(7, F.EV_CH_NAME) == "Ch7"
    with pytest.raises(F.FlpError):
        f.clone_channel(7, 160, "again")


def test_strip_notes_only_removes_named_channels():
    f = F.Flp(*F.parse(synthetic()))
    f.add_pattern(2, "Mixed", F.note_bytes(0, 2, 60) + F.note_bytes(96, 7, 36, 48))
    assert f.strip_notes({2}) == 2
    assert [len(v) for e, v in f.events if e == F.EV_PATNOTES] == [0, 24]


def test_pattern_id_collision_is_refused():
    f = F.Flp(*F.parse(synthetic()))
    f.add_pattern(100, "SUB 1", F.note_bytes(0, 7, 36, 24))
    with pytest.raises(F.FlpError):
        f.add_pattern(100, "ARP 1", F.note_bytes(0, 7, 36, 24))
    assert f.next_pattern_id(floor=100) == 101


def test_add_part_dedupes_identical_bars_and_places_clips():
    f = F.Flp(*F.parse(synthetic()))
    same = F.note_bytes(0, 7, 36, 24)
    other = F.note_bytes(96, 7, 43, 24)
    m = f.add_part("SUB", {4: same, 5: same, 6: other, 7: b""}, track=44, base_id=100)
    assert m == {4: 100, 5: 100, 6: 101}
    items = f.playlist_items()
    assert len(items) == 4
    starts = [struct.unpack("<I", it[0:4])[0] for it in items]
    assert starts == sorted(starts) and 4 * 384 in starts
    added = [it for it in items if struct.unpack("<H", it[6:8])[0] == F.PATTERN_BASE + 101][0]
    assert struct.unpack("<H", added[12:14])[0] == 499 - 44 and len({it[32:36] for it in items}) == 4
    assert F.emit(*F.parse(f.to_bytes())) == f.to_bytes()


def test_playlist_without_a_pattern_clip_uses_the_builtin_layout():
    data = synthetic()
    head, ev, tail = F.parse(data)
    ev[-1][1] = b""
    f = F.Flp(head, ev, tail)
    assert f.add_playlist_clips([(1, 2, 1, 3)]) == 1
    it = f.playlist_items()[0]
    assert len(it) == F.PLAYLIST_ITEM_SIZE and it[0:4] == struct.pack("<I", 2 * F.TICKS_PER_BAR)
    assert struct.unpack("<H", it[6:8])[0] == F.PATTERN_BASE + 1 and struct.unpack("<H", it[12:14])[0] == 499 - 3
    assert struct.unpack("<I", it[32:36])[0] == 1


def test_tempo_read_and_write():
    head, ev, tail = F.parse(synthetic())
    ev.insert(1, [156, struct.pack("<I", 130000)])
    f = F.Flp(head, ev, tail)
    assert f.tempo() == 130.0
    f.set_tempo(108.478)
    assert f.tempo() == 108.478
    with pytest.raises(F.FlpError):
        f.set_tempo(5)


def test_notes_by_bar_channels_merges_a_kit_in_position_order():
    got = F.notes_by_bar_channels([(0.5, 0.25, 60, 100, 3), (0.0, 0.25, 60, 100, 0), (4.0, 0.25, 60, 90, 3)])
    assert sorted(got) == [0, 1]
    first = got[0]
    assert len(first) == 2 * F.NOTE_SIZE and struct.unpack("<I", first[0:4])[0] == 0 and struct.unpack("<H", first[6:8])[0] == 0


def test_notes_by_bar_positions_are_bar_relative():
    out = F.notes_by_bar([(4.5, 0.5, 36, 100), (8.0, 1.0, 43, 90)], channel=7)
    assert sorted(out) == [1, 2]
    pos, _, ch, ln, key = struct.unpack("<IHHIH", out[1][:14])
    assert (pos, ch, ln, key) == (48, 7, 48, 36)


def test_not_flp_is_rejected():
    with pytest.raises(F.FlpError):
        F.parse(b"RIFF....")


def test_pattern_region_marker_is_not_a_channel():
    head, ev, tail = F.parse(synthetic())
    ev.insert(1, [64, struct.pack("<H", 3303)])
    ev.insert(2, [65, struct.pack("<H", 1)])
    f = F.Flp(head, ev, tail)
    assert f.channel_ids() == [2, 3, 7] and f.channel_count == 3
    f.clone_channel(7, 9, "New")
    assert f.channel_ids() == [2, 3, 7, 9]


def test_real_project_fixture_if_present():
    import os

    path = os.environ.get("COPRODUCER_FLP_FIXTURE")
    if not path or not os.path.isfile(path):
        pytest.skip("set COPRODUCER_FLP_FIXTURE to a sandbox copy of a real FL 2026 project")
    f = F.Flp.load(path)
    assert F.emit(*F.parse(f.to_bytes())) == f.to_bytes()
    assert len(f.channel_ids()) == f.channel_count


def test_fl26_event_172_has_three_bytes_before_the_title_text():
    """FL 26.1.7 starts a project with event 172 holding 3 bytes, then the title text event (id 192). Read as a dword it swallowed the text id,
    the rest of the file desynchronized, and a fresh project showed no playlist."""
    title = F.enc16("FL Studio 26.1.7.5654.5654")
    body = bytes([199, 12]) + b"26.1.7.5654\x00" + bytes([159]) + struct.pack("<I", 5654) + bytes([28, 1]) + bytes([172, 1, 1, 0])
    body += bytes([192, len(title)]) + title + bytes([156]) + struct.pack("<I", 130000)
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 0, 96)
    data = head + b"FLdt" + struct.pack("<I", len(body)) + body
    h, ev, t = F.parse(data)
    assert [e for e, _ in ev] == [199, 159, 28, 172, 192, 156]
    assert F.dec16(ev[4][1]).startswith("FL Studio") and F.emit(h, ev, t) == data


def test_import_channel_from_another_project_and_audio_clips():
    a = F.Flp(*F.parse(synthetic(channels=(2, 3))))
    b = F.Flp(*F.parse(synthetic(channels=(7,))))
    a.import_channel(b, 7, 9, "Imported", track=11)
    assert a.channel_ids() == [2, 3, 9] and a.channel_count == 3
    assert a.get_text(9, F.EV_CH_NAME) == "Imported" and struct.unpack("<H", a.events[a._find(9, F.EV_CH_TRACK)][1])[0] == 11
    with pytest.raises(F.FlpError):
        a.import_channel(b, 7, 9, "again")
    tmpl = _playlist_item(0, 1, 384, 3, 1)
    assert a.clear_playlist() == 1 and a.playlist_items() == []
    n = a.add_audio_clips(9, 6, [(768, 384, 1000.0, 2000.0), (0, 96, 0.0, 500.0)], tmpl)
    assert n == 2
    first, second = a.playlist_items()
    assert struct.unpack("<I", first[0:4])[0] == 0 and struct.unpack("<H", first[6:8])[0] == 9 and struct.unpack("<H", first[12:14])[0] == 499 - 6
    assert struct.unpack("<ff", second[24:32]) == (1000.0, 2000.0) and struct.unpack("<I", second[8:12])[0] == 384
    assert struct.unpack("<I", first[32:36])[0] != struct.unpack("<I", second[32:36])[0]


def test_remove_channel_updates_count_and_keeps_the_rest():
    f = F.Flp(*F.parse(synthetic()))
    f.remove_channel(3)
    g = F.Flp(*F.parse(f.to_bytes()))
    assert g.channel_ids() == [2, 7] and g.channel_count == 2
    assert g.get_text(7, F.EV_CH_NAME) == "Ch7"
    with pytest.raises(F.FlpError):
        g.block(3)


def test_mixer_volume_records_are_read_and_set():
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 0, 96)
    recs = b"".join(struct.pack("<IHHI", 0, 8128, 0x7000 + 64 * t, 12800) for t in (0, 1, 2))
    f = F.Flp(*F.parse(F.emit(head, [[199, F.enc16("26.1.7")], [225, recs], [99, b"\x00\x00"]], b"")))
    assert f.mixer_volume(2) == 12800 and f.mixer_volume(5) is None
    f.set_mixer_volume(2, 9000)
    g = F.Flp(*F.parse(f.to_bytes()))
    assert g.mixer_volume(2) == 9000 and g.mixer_volume(1) == 12800
    with pytest.raises(F.FlpError):
        g.set_mixer_volume(9, 1)


def test_song_mode_flag():
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 0, 96)
    f = F.Flp(*F.parse(F.emit(head, [[199, F.enc16("26.1.7")], [9, b"\x00"], [99, b"\x00\x00"]], b"")))
    assert f.song_mode() is False
    f.set_song_mode(True)
    assert F.Flp(*F.parse(f.to_bytes())).song_mode() is True


def test_renumber_channels_closes_gaps_in_notes_and_clips():
    data = bytearray(synthetic((2, 3, 7)))
    f = F.Flp(*F.parse(bytes(data)))
    f.strip_notes(set())
    f.add_pattern(5, "P", F.note_bytes(0, 7, 60) + F.note_bytes(96, 3, 62))
    audio = bytearray(88)
    audio[6:8] = struct.pack("<H", 7)
    audio[32:36] = struct.pack("<I", 9)
    f.events[f._playlist_index()][1] += bytes(audio)
    m = f.renumber_channels()
    g = F.Flp(*F.parse(f.to_bytes()))
    assert m == {2: 0, 3: 1, 7: 2} and g.channel_ids() == [0, 1, 2]
    assert g.get_text(2, F.EV_CH_NAME) == "Ch7"
    chans = []
    for i in g._note_events():
        v = g.events[i][1]
        chans += [struct.unpack("<H", v[k + 6 : k + 8])[0] for k in range(0, len(v), F.NOTE_SIZE)]
    assert chans == [0, 2, 1]
    assert [struct.unpack("<H", it[6:8])[0] for it in g.playlist_items()][-1] == 2


def test_event_172_with_five_byte_value_keeps_the_stream_in_step():
    """FL 26.1.7.5654 writes its second event 172 as 5 bytes, followed by event 237 (16 bytes). Read as 4 bytes, every later event shifts and the channel blocks are lost."""
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 1, 96)
    body = bytes([172, 0, 1, 0, 0, 0]) + bytes([237, 16]) + bytes(16) + bytes([64, 3, 0]) + bytes([0, 1]) + bytes([203, 4]) + F.enc16("A")
    data = head + b"FLdt" + struct.pack("<I", len(body)) + body
    h, ev, t = F.parse(data)
    assert [e for e, _ in ev] == [172, 237, 64, 0, 203]
    assert F.emit(h, ev, t) == data
    assert F.Flp(h, ev, t).channel_ids() == [3]


def _two_arrangements():
    from coproducer import testflp

    f = testflp.with_organization(testflp.project({0: "Kick", 1: "Vox"}, {0: [0]}, bars=2), inserts=2, rows=3)
    f.add_audio_clips(1, 2, [(0, 384, 0.0, 500.0)], F.PATTERN_CLIP_TEMPLATE)
    return testflp.with_second_arrangement(f, name="Different Chords")


def test_the_current_arrangement_is_read_and_edited_not_the_first():
    # Found on the FL demo "Future House" (2026-10-25): two arrangements, event 100 names the second, and FL plays that one.
    f = _two_arrangements()
    arrs = f.arrangements()
    assert [a["id"] for a in arrs] == [0, 1] and f.current_arrangement()["name"] == "Different Chords"
    first = bytes(f.events[arrs[0]["playlist"]][1])
    f.add_playlist_clips([(1, 4, 1, 1)])
    assert bytes(f.events[arrs[0]["playlist"]][1]) == first  # the first arrangement is left alone
    assert len(f.playlist_items()) == len(first) // F.PLAYLIST_ITEM_SIZE + 1
    g = F.Flp(*F.parse(f.to_bytes()))
    assert len(g.playlist_items()) == len(f.playlist_items())


def test_renumbering_updates_audio_clips_in_every_arrangement():
    f = _two_arrangements()
    vox = f._starts()[1]
    f.events[vox][1] = struct.pack("<H", 7)  # a gap: ids 0 and 7, with the audio clips still pointing at 1
    f._map_all_playlists(lambda items: [it[:6] + struct.pack("<H", 7) + it[8:] if struct.unpack("<H", it[6:8])[0] == 1 else it for it in items])
    assert f.renumber_channels() == {0: 0, 7: 1}
    for i in f._playlist_indexes():
        v = f.events[i][1]
        refs = [struct.unpack("<H", v[k + 6 : k + 8])[0] for k in range(0, len(v), F.PLAYLIST_ITEM_SIZE)]
        assert 1 in refs and 7 not in refs


def test_rows_and_markers_come_from_the_current_arrangement():
    from coproducer import flporg

    f = _two_arrangements()
    flporg.set_playlist_track(f, 1, name="Drums", rgb=(76, 175, 80))
    arrs = f.arrangements()
    first_rows = [bytes(v) for e, v in f.events[arrs[0]["start"] : arrs[0]["end"]] if e == 239]
    assert first_rows == [] and flporg.track_name(f, 1) == "Drums"
    cur = f.current_arrangement()
    f.events[cur["playlist"] + 1 : cur["playlist"] + 1] = [[F.EV_MARKER_POS, struct.pack("<I", 8 * 384)], [F.EV_MARKER_NAME, F.enc16("Drop")]]
    assert f.time_markers() == [{"pos": 3072, "name": "Drop"}]


def test_time_markers_are_written_as_fl_writes_them_and_kept_in_order():
    from coproducer import testflp

    f = testflp.with_organization(testflp.project({0: "Kick"}, {0: [0]}, bars=4), inserts=1, rows=2)
    f.add_time_marker(8 * 384, "Drop")
    f.add_time_marker(0, "Build")
    f.add_time_marker(16 * 384, "Outro")
    assert [(m["pos"], m["name"]) for m in f.time_markers()] == [(0, "Build"), (3072, "Drop"), (6144, "Outro")]
    pl = f.current_arrangement()["playlist"]
    assert [e for e, _v in f.events[pl + 1 : pl + 9]] == [148, 33, 34, 46, 45, 168, 101, 205]
    g = F.Flp(*F.parse(f.to_bytes()))
    assert len(g.time_markers()) == 3 and f.events[pl + 25][0] == 238


def test_channel_pitch_widens_the_knob_range_and_layers_follow_renumbering():
    import struct as st

    from coproducer import automation, testflp
    f = testflp.project({0: "Kick", 1: "Gone", 2: "Kick B", 3: "Snare"}, {0: [0, 96], 3: [48]})
    assert f.channel_pitch(2) == (0, 2)
    f.set_channel_pitch(2, -350)
    assert f.channel_pitch(2) == (-350, 4)  # FL clamps the knob to its range, so the range grows to hold the value
    f.set_channel_pitch(2, 120)
    assert f.channel_pitch(2) == (120, 4)  # never narrowed
    f.set_layer_children(0, [2, 3])
    assert f.layer_children(0) == [2, 3] and f.channel_type(0) is None
    assert f.move_notes(0, 3) == 2 and sorted(n[1] for ns in f.pattern_notes().values() for n in ns) == [3, 3, 3]
    automation.add_automation_clip(f, 9, "Snare pitch", automation.channel_link(3, 4), [(0, 0.5), (4, 1.0)], track=2, bipolar=True)
    f.remove_channel(1)
    mapping = f.renumber_channels()
    assert mapping == {0: 0, 2: 1, 3: 2, 9: 3} and f.layer_children(0) == [1, 2]
    link = next(bytes(v) for e, v in f.events if e == 227)
    assert st.unpack_from("<HHII", link)[1:4:2] == (3, 2 << 16 | 4)  # the clip's own id and the channel it drives both moved
    with pytest.raises(F.FlpError):
        f.set_channel_pitch(1, 5000)


def test_window_playlist_moves_a_stretch_to_the_start_and_cuts_items_by_their_offsets():
    f = F.Flp(*F.parse(synthetic(channels=(2, 5))))
    f.events.insert(1, [156, struct.pack("<I", 120000)])   # 120 bpm: a tick is 60000 / 120 / 96 ms
    f.events.insert(f.block(5)[0] + 1, [21, b"\x05"])      # channel 5 is an automation clip
    auto = bytearray(_playlist_item(0, 0, 384 * 8, 1, 2))
    auto[6:8] = struct.pack("<H", 5)
    auto[24:32] = struct.pack("<ff", -1.0, -1.0)
    audio = bytearray(_playlist_item(384 * 3, 0, 384 * 2, 2, 3))
    audio[6:8] = struct.pack("<H", 2)
    audio[24:32] = struct.pack("<ff", 0.0, 4000.0)
    pat = bytearray(_playlist_item(384 * 2, 1, 384 * 4, 3, 4))          # a one-bar pattern looped four times from bar 2
    pat[24:32] = struct.pack("<ii", -1, -1)
    slip = bytearray(_playlist_item(384 * 3, 1, 384 * 2, 4, 6))         # two bars of a pattern window that starts half a bar in
    slip[24:32] = struct.pack("<ii", 192, 192 + 384 * 2)
    late = _playlist_item(384 * 9, 1, 384, 3, 5)
    f.events[f._playlist_index()][1] = b"".join([bytes(auto), bytes(pat), bytes(audio), bytes(slip), late])
    assert f.pattern_lengths() == {1: 384}
    r = f.window_playlist(384 * 4, 384 * 6)
    assert r == {"kept": 5, "removed": 1, "cut": 4}
    items = f.playlist_items()
    got = {struct.unpack("<I", it[32:36])[0]: it for it in items}
    a2 = got[2]
    assert struct.unpack("<I", a2[0:4])[0] == 0 and struct.unpack("<I", a2[8:12])[0] == 768
    assert struct.unpack("<ff", a2[24:32]) == (16.0, 24.0)               # automation: beats 16 to 24 of the clip
    au = got[3]
    assert struct.unpack("<I", au[0:4])[0] == 0 and struct.unpack("<I", au[8:12])[0] == 384
    assert struct.unpack("<ff", au[24:32]) == pytest.approx((2000.0, 4000.0))   # audio: one bar in at 120 bpm is 2 s
    loops = sorted((struct.unpack("<I", it[0:4])[0], struct.unpack("<I", it[8:12])[0], struct.unpack("<ii", it[24:32])) for it in items
                   if struct.unpack("<H", it[12:14])[0] == 499 - 3)
    assert loops == [(0, 384, (0, 384)), (384, 384, (0, 384))]          # the loop unrolled: one clip per pass, none loops from a cut edge
    assert len({struct.unpack("<I", it[32:36])[0] for it in items}) == len(items)
    sl = got[6]
    assert struct.unpack("<I", sl[0:4])[0] == 0 and struct.unpack("<ii", sl[24:32]) == (576, 960)
    with pytest.raises(F.FlpError):
        f.window_playlist(10, 10)


def test_set_data_folder_round_trips_and_needs_the_event():
    f = F.Flp(*F.parse(synthetic()))
    assert f.data_folder() is None
    with pytest.raises(F.FlpError):
        f.set_data_folder("C:\\work")
    f.events.append([F.EV_DATA_FOLDER, F.enc16("C:\\old\\")])
    f.set_data_folder("C:\\coproducer\\sandbox\\bench")
    assert f.data_folder() == "C:\\coproducer\\sandbox\\bench\\"
    again = F.Flp(*F.parse(f.to_bytes()))
    assert again.data_folder() == "C:\\coproducer\\sandbox\\bench\\"


def test_reset_playlist_tracks_unmutes_ungroups_and_unnames_rows():
    f = F.Flp(*F.parse(synthetic()))
    plain = bytes.fromhex("060000004851560000000000010000803ff0ffffff0000000000000000000500000000000000010000000000000000000000000000ffffffffffffffff010000000000000000")
    muted = bytearray(plain)
    muted[0], muted[12] = 1, 0
    grouped = bytearray(plain)
    grouped[0], grouped[8], grouped[46] = 2, 4, 1
    f.events += [[F.EV_TRACK, bytes(muted)], [43, b"\x00"], [F.EV_TRACK, bytes(grouped)], [43, b"\x00"], [F.EV_TRACK_NAME, F.enc16("Drums")],
                 [F.EV_TRACK, plain], [43, b"\x00"]]
    assert f.reset_playlist_tracks() == 3
    g = F.Flp(*F.parse(f.to_bytes()))
    rows = [bytes(v) for e, v in g.events if e == F.EV_TRACK]
    assert [r[12] for r in rows] == [1, 1, 1] and [r[46] for r in rows] == [0, 0, 0] and rows[1][8:12] == bytes(4) and rows[2] == plain
    assert not any(e == F.EV_TRACK_NAME for e, _ in g.events)
