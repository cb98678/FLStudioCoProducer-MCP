import struct

import numpy as np

from coproducer import drumplan as D
from coproducer import flpfile as F
from coproducer import oneshots as O
from coproducer import tension as T

SECTIONS = [
    {"name": "intro", "start": 0, "end": 4}, {"name": "kickin", "start": 4, "end": 8}, {"name": "groove", "start": 8, "end": 24},
    {"name": "break", "start": 24, "end": 28}, {"name": "build", "start": 28, "end": 32}, {"name": "drop", "start": 32, "end": 43},
    {"name": "main", "start": 43, "end": 62}, {"name": "outro", "start": 62, "end": 65},
]
CH = {"kick": 2, "snare": 3, "clap": 4, "hat": 5, "ohat": 46, "shaker": 0, "rim": 1, "crash": 45, "tom": 6}


def test_every_voice_is_finite_normalized_and_deterministic():
    for name, fn in O.KIT.items():
        a, b = fn(), fn()
        assert np.isfinite(a).all() and abs(np.max(np.abs(a)) - 1.0) < 1e-6 and np.array_equal(a, b), name


def test_write_kit_makes_eleven_wavs(tmp_path):
    files = O.write_kit(tmp_path)
    assert len(files) == 11 and all(p.stat().st_size > 1000 for p in files.values())   # nine voices and, since the demo study, perc and ride


def test_fx_voices_have_requested_length_and_stereo():
    assert O.sweep_noise(0.5, 300, 9000).shape == (int(0.5 * O.SR), 2)
    assert O.tone_riser(0.5, 200, 800).shape[1] == 2 and O.reverse_crash(0.5).shape == (int(0.5 * O.SR), 2)


def test_build_has_rising_roll_density_and_no_kick_in_last_bar():
    p = D.plan_drums(SECTIONS)
    snares = [sum(1 for e in p.events if e[0] == b and e[2] == "snare") for b in range(28, 32)]
    assert snares == sorted(snares) and snares[-1] > 2 * snares[0]
    assert not [e for e in p.events if e[0] == 31 and e[2] == "kick"]


def test_drop_has_backbeat_and_crash_with_default_crashes():
    p = D.plan_drums(SECTIONS, crashes=D.default_crashes(SECTIONS))
    assert any(e[0] == 32 and e[2] == "crash" for e in p.events)
    assert {(e[1]) for e in p.events if e[0] == 33 and e[2] == "clap"} == {4.0, 12.0}


def test_unknown_section_is_rejected():
    try:
        D.plan_drums([{"name": "wobble", "start": 0, "end": 1}])
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_fx_cues_cover_break_build_and_drop():
    kinds = {(c["kind"], c["bar"]) for c in D.fx_cues(SECTIONS)}
    assert ("noise_riser", 24) in kinds and ("tone_riser", 28) in kinds and ("impact", 32) in kinds and ("downlifter", 32) in kinds


def test_drum_plan_bytes_use_sampler_channels_and_bar_relative_ticks():
    p = D.plan_drums(SECTIONS)
    by = D.to_note_bytes(p, CH)
    d = by[33]
    rows = [struct.unpack("<IHHIH", d[k : k + 14]) for k in range(0, len(d), 24)]
    assert all(r[1] == 0x4000 and r[2] in CH.values() and 0 <= r[0] < 384 for r in rows)
    assert [r[0] for r in rows if r[2] == 2] == [0, 96, 192, 288]


def test_drum_pattern_round_trip_through_flp():
    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, 1, 96)
    pl = bytearray(88)
    pl[6:8] = struct.pack("<H", F.PATTERN_BASE + 1)
    ev = [[65, struct.pack("<H", 1)], [224, b""], [64, struct.pack("<H", 2)], [0, b"\x01"], [99, b"\0\0"], [233, bytes(pl)]]
    f = F.Flp(head, ev, b"")
    m = f.add_part("DR", D.to_note_bytes(D.plan_drums(SECTIONS), CH), track=43, base_id=30)
    assert len(m) == 65 and len(set(m.values())) < 65 and min(m.values()) == 30
    assert F.emit(*F.parse(f.to_bytes())) == f.to_bytes()


def test_tension_build_shape():
    bass, arp = T.drop_build(24, 4, 28, 4, 36, 48, [[57, 60, 65], [60, 65, 69], [65, 69, 72], [69, 72, 77]])
    assert min(n[0] for n in bass) == 24 * 4 and max(n[0] for n in bass) < 33 * 4
    swell = [n for n in bass if n[2] == 36 and n[1] == 3.9]
    assert [n[3] for n in swell] == sorted(n[3] for n in swell)
    assert len(arp) == 64 and arp[-1][3] > arp[0][3]


def test_truncate_at_kicks_cuts_and_drops_short_notes():
    notes = [(0.0, 2.0, 36, 100), (1.9, 0.5, 36, 100)]
    out = T.truncate_at_kicks(notes, [1.0, 2.0])
    assert out[0][1] < 1.0 and len(out) == 1


def test_shift_beats_drops_negative_starts():
    assert T.shift_beats([(0.25, 1, 36, 90), (1.0, 1, 36, 90)], -0.5) == [(0.5, 1, 36, 90)]
