"""Automation clips in an FLP. The golden bytes below are what FL Studio 26.1.7 wrote itself (2026-10-22) for a stereo separation clip on
Insert 1 (bipolar knob, 0.5, 57.5 beats) and for the matching link event."""
import struct

import pytest

from coproducer import automation as A
from coproducer import flpfile as F
from coproducer.flpfile import Flp, FlpError
from coproducer.testrig import synthetic_flp

FL_234 = bytes.fromhex(
    "0100000040000000010400000003000000020000000000000000000000000000000000e03f00000000000000000000000000c04c40000000000000e03f0000000000000002")
FL_227 = bytes.fromhex("00000d0000000000c21f407008000000d5010000")


def base(channels=(0, 1)):
    return synthetic_flp(channels)


def test_link_layout():
    assert A.mixer_link(1, A.P_STEREO_SEP) == 0x70401FC2
    assert A.mixer_link(0, A.P_EQ_LOW_FREQ, sub=9) == 0x70091FD8
    assert A.mixer_link(1, A.PLUGIN_PARAM_BASE) == 0x70408000
    assert A.decode_link(0x70801FC2) == {"track": 2, "sub": 0, "param": 0x1FC2}
    with pytest.raises(FlpError):
        A.mixer_link(128)


def test_link_event_matches_fl():
    assert A.encode_link(13, 0x70401FC2) == FL_227


def test_points_match_fl_bytes():
    assert A.encode_points([(0.0, 0.5), (57.5, 0.5)], bipolar=True)[: len(FL_234)] == FL_234
    assert len(A.encode_points([(0.0, 0.5), (57.5, 0.5)])) == 181


def test_points_round_trip_uses_absolute_beats():
    pts = [(0.0, 0.8), (4.0, 0.8), (4.5, 0.0), (10.0, 0.3)]
    enc = A.encode_points(pts)
    assert struct.unpack_from("<d", enc, 21 + 24 * 2)[0] == 0.5  # stored as the gap from the previous point
    back = A.decode_points(enc)
    assert [(round(b, 6), round(v, 6)) for b, v, _ in back] == pts


@pytest.mark.parametrize("pts", [[(0.0, 0.5)], [(1.0, 0.5), (2.0, 0.5)], [(0.0, 0.5), (2.0, 0.5), (1.0, 0.5)], [(0.0, 1.5), (1.0, 0.5)]])
def test_bad_points_refused(pts):
    with pytest.raises(FlpError):
        A.encode_points(pts)


def test_add_list_remove():
    f = base()
    n = A.add_automation_clip(f, 5, "Insert 1 - Volume", A.mixer_link(1), [(0.0, 0.8), (8.0, 0.3)], track=2)
    assert n == 1 and f.channel_count == 3
    [c] = A.list_automation(f)
    assert c["channel"] == 5 and c["name"] == "Insert 1 - Volume" and c["link"] == 0x70401FC0
    assert [(round(b, 3), round(v, 3)) for b, v, _ in c["points"]] == [(0.0, 0.8), (8.0, 0.3)]
    it = f.playlist_items()[0]
    assert struct.unpack("<I", it[0:4])[0] == 0 and struct.unpack("<H", it[6:8])[0] == 5
    assert struct.unpack("<I", it[8:12])[0] == 8 * 96 and struct.unpack("<H", it[12:14])[0] == 499 - 2
    again = Flp(*F.parse(f.to_bytes()))
    assert [c["channel"] for c in A.list_automation(again)] == [5] and again.to_bytes() == f.to_bytes()
    A.remove_automation_clip(f, 5)
    assert A.list_automation(f) == [] and f.channel_count == 2 and f.playlist_items() == []
    assert not [e for e in f.events if e[0] == A.EV_LINK]


def test_links_sit_before_first_channel_in_order():
    f = base()
    A.add_automation_clip(f, 5, "a", A.mixer_link(1), [(0.0, 0.5), (4.0, 0.5)])
    A.add_automation_clip(f, 6, "b", A.mixer_link(2, A.P_PAN), [(0.0, 0.5), (4.0, 0.5)], bipolar=True)
    ids = [e for e, _ in f.events]
    first_ch = ids.index(64)
    ctl = [i for i, e in enumerate(ids) if e in (226, A.EV_LINK)]
    assert max(ctl) < first_ch  # every 226 and 227 moved ahead of the first channel block
    links = [bytes(v) for e, v in f.events if e == A.EV_LINK]
    assert [struct.unpack_from("<H", l, 2)[0] for l in links] == [5, 6]
    item_ids = [struct.unpack("<I", it[32:36])[0] for it in f.playlist_items()]
    assert sorted(item_ids) == [1, 2]


def test_duplicate_channel_id_refused():
    f = base()
    with pytest.raises(FlpError):
        A.add_automation_clip(f, 1, "x", A.mixer_link(1), [(0.0, 0.5), (1.0, 0.5)])


def test_fader_law():
    assert A.db_to_fader(0) == pytest.approx(0.8)
    assert A.db_to_fader(-15.4) == pytest.approx(0.3)
    assert A.db_to_fader(-200) == 0.0 and A.db_to_fader(float("-inf")) == 0.0
    assert A.db_to_fader(12) == 1.0
    for db in (-40, -19.05, -12, -3, 0, 4):
        assert A.fader_to_db(A.db_to_fader(db)) == pytest.approx(db, abs=0.01)
    assert A.fader_to_db(0.0) == float("-inf")


def test_ramp_and_duck_points():
    assert A.ramp_points(8, 0.0, 0.8) == [(0.0, 0.0), (8.0, 0.8)]
    with pytest.raises(FlpError):
        A.ramp_points(0, 0, 1)
    pts = A.duck_points(16, [(4, 6), (10, 12)], 0.8, 0.3)
    assert pts[0] == (0.0, 0.8) and pts[-1] == (16.0, 0.8)
    assert [p[0] for p in pts] == sorted(p[0] for p in pts)
    assert (4, 0.3) in pts and (6, 0.3) in pts and (10, 0.3) in pts
    A.encode_points(pts)  # accepted by the encoder
    assert A.duck_points(8, [(0, 2)], 0.8, 0.3)[0] == (0.0, 0.3)
    for bad in ([(6, 4)], [(4, 20)], [(0.05, 2)], [(4, 6), (6.05, 8)]):
        with pytest.raises(FlpError):
            A.duck_points(16, bad, 0.8, 0.3)


def test_no_em_dash_in_module():
    import pathlib
    assert "—" not in pathlib.Path(A.__file__).read_text(encoding="utf-8")


def test_clip_windows_merge_and_sample_marker():
    f = base((0, 1, 2))
    # channel 1 gets a sample path; playlist holds clips of channels 1 and 2
    for i, (e, v) in enumerate(f.events):
        if e == 64 and struct.unpack("<H", bytes(v))[0] == 1:
            f.events.insert(i + 1, [196, F.enc16("C:\\x\\VC\\a.wav")])
            break

    def item(pos, ch, ln, tr, iid):
        it = bytearray(88)
        it[0:4] = struct.pack("<I", pos); it[6:8] = struct.pack("<H", ch); it[8:12] = struct.pack("<I", ln)
        it[12:14] = struct.pack("<H", 499 - tr); it[32:36] = struct.pack("<I", iid)
        return bytes(it)

    f.events[f._playlist_index()][1] = b"".join([item(0, 1, 4 * 96, 1, 1), item(4 * 96 + 48, 1, 4 * 96, 1, 2), item(40 * 96, 1, 96, 1, 3), item(0, 2, 96, 2, 4)])
    assert A.channels_with_sample(f, "\\vc\\") == [1]
    assert A.clip_windows(f, [1], gap=0.5) == [(0.0, 8.5), (40.0, 41.0)]
    assert A.clip_windows(f, [1, 2], gap=0.0)[:2] == [(0.0, 4.0), (4.5, 8.5)]
    assert A.clip_windows(f, [9]) == []


def test_link_formula_text_stays_with_its_link_and_is_removed_with_it():
    f = base()
    first = next(i for i, (e, _) in enumerate(f.events) if e == 64)
    old = [[227, A.encode_link(9, 0x300011)], [230, F.enc16("0.5*Tension(")], [227, A.encode_link(9, 0x3D0011)], [230, F.enc16("0.5-0.5*Tension(")]]
    f.events[first:first] = old
    A.add_automation_clip(f, 5, "n", A.mixer_link(1), [(0.0, 0.5), (4.0, 0.5)])
    seq = [(e, bytes(v)) for e, v in f.events if e in (226, 227, 230)]
    assert [e for e, _ in seq] == [226, 226, 226, 227, 230, 227, 230, 227]
    assert seq[4][1] == F.enc16("0.5*Tension(") and seq[6][1] == F.enc16("0.5-0.5*Tension(")
    A.remove_automation_clip(f, 5)
    assert [e for e, _ in [(e, v) for e, v in f.events if e in (226, 227, 230)]] == [226, 226, 226, 227, 230, 227, 230]
    # removing a clip that owns a formula drops the formula too
    g = base()
    A.add_automation_clip(g, 5, "n", A.mixer_link(1), [(0.0, 0.5), (4.0, 0.5)])
    i = next(i for i, (e, v) in enumerate(g.events) if e == 227)
    g.events.insert(i + 1, [230, F.enc16("x")])
    A.remove_automation_clip(g, 5)
    assert not [e for e, _ in g.events if e in (227, 230)]
