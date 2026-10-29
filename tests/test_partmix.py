import numpy as np
import pytest
import soundfile as sf

from coproducer import partmix
from coproducer.testflp import project


def test_roles_from_names():
    names = {"Kick": "kick", "909 CH 2": "hats", "707 OH": "hats", "Chord Stab": "stab", "Chop hook #2": "chops", "Rising Arp": "arp", "Sub Bass": "sub",
             "Reese Bass": "reese", "Vocal 124 bpm": "vocal", "FX bed": "fx", "Snare": "clap", "CP_Chop_hook_2": "chops", "Mystery": None,
             "Drill 808": "bass", "808 Snare": "clap", "808 Kick": "kick", "Stab - Demo Pluck": "stab", "Pluck - Saku": "arp", "Bass - DX10 log drum": "bass"}
    for n, r in names.items():
        assert partmix.role_of(n) == r, n


def test_solo_projects_enable_only_one_track():
    f = project({0: "Kick", 1: "Chord Stab"}, {0: [0], 1: [0]})
    f.set_track(1, 7)  # kick stays on track 3 (fixture), stab moves to 7
    solos = partmix.solo_projects(f, "p")
    assert {s["role"] for s in solos.values()} == {"kick", "stab"}
    from coproducer import flpfile
    for t, s in solos.items():
        g = flpfile.Flp(*flpfile.parse(s["flp"]))
        on = [g.channel_info(c)["name"] for c in g.channel_ids() if g.channel_info(c)["enabled"]]
        assert on == [g.channel_info(c)["name"] for c in s["channels"]]


def test_profile_and_plan():
    levels = {1: {"lufs": -10.0}, 6: {"lufs": -14.0}, 7: {"lufs": -40.0}, 9: {"lufs": -20.0}, 12: {"lufs": -20.0}, 0: {"lufs": -20.0}}
    roles = {1: "kick", 6: "sub", 7: "stab", 9: "chops", 12: "chops", 0: "chops"}
    prof = {"reference": "kick", "relative_db": {"sub": -4.0, "stab": -12.0, "chops": -7.0}}
    ch = partmix.plan_changes(levels, roles, {1: 0.0, 6: -4.0, 7: -9.0, 9: -1.0, 12: -1.0, 0: -1.0}, prof)
    by = {c["track"]: c for c in ch}
    assert 6 not in by                         # already at -4 relative
    assert by[7]["role_delta_db"] == 12.0      # wants +18, capped at 12
    assert 0 not in by                         # the master is never touched
    # three chop tracks at -20 each sum to -15.2: 8.2 dB under the kick, target is -7, so about -1.2 dB
    assert abs(by[9]["role_delta_db"] - (-10 - 7 + 15.23)) < 0.1 and by[9]["role_delta_db"] == by[12]["role_delta_db"]


def test_profile_round_trip_and_errors():
    prof = partmix.profile_from({1: {"lufs": -10.0}, 2: {"lufs": -13.0}}, {1: "kick", 2: "clap"})
    assert prof["relative_db"] == {"kick": 0.0, "clap": -3.0}
    with pytest.raises(ValueError):
        partmix.profile_from({2: {"lufs": -13.0}}, {2: "clap"})


def test_part_level(tmp_path):
    x = 0.1 * np.sin(2 * np.pi * 220 * np.arange(48000 * 3) / 48000)
    sf.write(tmp_path / "a.wav", np.column_stack([x, x]), 48000)
    lv = partmix.part_level(str(tmp_path / "a.wav"))
    assert -25 < lv["lufs"] < -15 and abs(lv["peak_db"] + 20) < 0.5


def test_solos_keep_layer_parents_controllers_and_clips_and_can_bypass_the_master():
    # Found on the FL demo "Future House" (2026-10-25): the kick solo rendered silent (its notes are on a Layer channel), the pump stopped (an
    # Envelope Controller on the master track was disabled) and every solo hit the master limiter.
    import struct

    from coproducer import flpfile as F
    from coproducer import partmix, testflp

    f = testflp.with_mixer(testflp.project({0: "KICK", 1: "Kick A", 2: "Bass", 3: "Pump", 4: "Clip"}, {0: [0]}, bars=1))
    starts = f._starts()
    adds = {0: [[21, b"\x03"], [94, struct.pack("<H", 1)]], 3: [[21, b"\x02"], [201, F.enc16("Fruity Envelope Controller")]], 4: [[21, b"\x05"]]}
    for ch in sorted(adds, reverse=True):
        f.events[starts[ch] + 1 : starts[ch] + 1] = adds[ch]
    for ch, track in ((0, 0), (1, 1), (2, 2), (3, 0), (4, 0)):
        f.set_track(ch, track)
    rec = b"".join(struct.pack("<IHHI", 0, 0x1F00, 0x7000 + s, 1) for s in range(10))  # master slot-enabled records
    f.events[f._mixer_index()][1] = bytes(f.events[f._mixer_index()][1]) + rec
    solos = partmix.solo_projects(f, "p", bypass_master=True)
    assert set(solos) == {1, 2}  # the master holds only the Layer, the controller and the clip, so it is not a part
    kick = F.Flp(*F.parse(solos[1]["flp"]))
    on = {c: kick.channel_info(c)["enabled"] for c in kick.channel_ids()}
    assert on == {0: True, 1: True, 2: False, 3: True, 4: True}
    v = kick.events[kick._mixer_index()][1]
    slots = [struct.unpack("<IHHI", v[k : k + 12]) for k in range(0, len(v) - 11, 12)]
    assert all(r[3] == 0 for r in slots if r[1] & 0xFF == 0 and 0x7000 <= r[2] < 0x7000 + 10)


def test_a_part_named_only_by_its_insert_gets_its_role_from_the_insert():
    from coproducer import flpfile as F
    from coproducer import partmix, testflp

    f = testflp.project({0: "Laurie Webb Baby"}, {0: [0]}, bars=1)
    f.set_track(0, 1)
    for n, name in enumerate([None, "Vocal Chop"]):
        f.events += [[149, bytes(4)]] + ([[204, F.enc16(name)]] if name else []) + [[236, bytes(12)], [235, b"\x01"], [147, bytes(4)]]
    assert partmix.solo_projects(f, "p")[1]["role"] == "chops"
