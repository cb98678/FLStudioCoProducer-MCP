import struct

import pytest

from coproducer import anatomy, fxlib
from coproducer import flpfile as F
from coproducer import testflp


def mixer_project(slots: dict) -> F.Flp:
    """A project with a mixer section in FL 26's order; every insert has ten slot markers (event 98), slots {insert: {slot: plugin}} are filled."""
    f = testflp.with_mixer(testflp.project({0: "Kick"}, {0: [0]}, bars=1), tracks=4)
    for n in range(4):
        f.events += [[149, bytes(4)], [42, b"\x01"]] + ([[204, F.enc16("Insert %d" % n)]] if n else []) + [[236, bytes(12)]]
        for s in range(10):
            plug = slots.get(n, {}).get(s)
            if plug:
                f.events += [[201, F.enc16(plug)], [212, struct.pack("<II", n, s) + bytes(44)], [155, bytes(4)], [128, bytes(4)], [41, b"\x00"],
                             [213, ("state of %s" % plug).encode()]]
            f.events.append([98, struct.pack("<H", s)])
        f.events += [[235, b"\x01"], [147, bytes(4)]]
    rec = b"".join(struct.pack("<IHHI", 0, 0x1F00, 0x7000 + 64 * n + s, 0) for n in range(4) for s in range(10))
    f.events[f._mixer_index()][1] = bytes(f.events[f._mixer_index()][1]) + rec
    return f


def test_extract_and_inject_moves_the_whole_state_and_rewrites_the_wrapper(tmp_path):
    src = mixer_project({1: {2: "Fruity Reeverb 2"}})
    entry = fxlib.extract(src, 1, 2, "test verb", "src.flp", {"Decay time": "1.0sec"})
    assert entry["plugin"] == "Fruity Reeverb 2" and entry["params"] == {"Decay time": "1.0sec"}
    dst = mixer_project({3: {0: "Fruity Limiter"}})
    fxlib.inject(dst, 3, 4, entry)
    g = F.Flp(*F.parse(dst.to_bytes()))
    ins = anatomy.inserts(g)[3]
    assert [(s["slot"], s["plugin"]) for s in ins["slots"]] == [(0, "Fruity Limiter"), (4, "Fruity Reeverb 2")]
    run = fxlib._run(g, 3, 4)
    wrapper = next(bytes(v) for e, v in g.events[run[0] : run[1]] if e == 212)
    assert struct.unpack_from("<II", wrapper, 0) == (3, 4)
    assert next(bytes(v) for e, v in g.events[run[0] : run[1]] if e == 213) == b"state of Fruity Reeverb 2"
    v = g.events[g._mixer_index()][1]
    on = [struct.unpack("<IHHI", v[k : k + 12])[3] for k in range(0, len(v) - 11, 12) if struct.unpack("<IHHI", v[k : k + 12])[2] == 0x7000 + 64 * 3 + 4]
    assert on == [1]
    p = fxlib.save_entry(entry, tmp_path)
    assert p.name == "test_verb.json" and fxlib.load_entry("Test Verb", tmp_path)["plugin"] == "Fruity Reeverb 2"
    assert fxlib.list_entries(tmp_path)[0]["name"] == "test verb"


def test_inject_refuses_a_taken_slot_and_extract_refuses_an_empty_one():
    f = mixer_project({1: {0: "Fruity Balance"}})
    entry = fxlib.extract(f, 1, 0, "bal")
    with pytest.raises(F.FlpError, match="already holds Fruity Balance"):
        fxlib.inject(f, 1, 0, entry)
    with pytest.raises(F.FlpError, match="empty"):
        fxlib.extract(f, 2, 0, "nothing")
    with pytest.raises(F.FlpError, match="not in the file"):
        fxlib.inject(f, 9, 0, entry)


def test_the_shipped_library_entries_are_well_formed():
    entries = fxlib.list_entries()
    assert len(entries) >= 50
    for e in entries:
        full = fxlib.load_entry(e["name"])
        if e["kind"] == "channel":
            assert full["events"][0][0] == 64 and any(x[0] == 201 for x in full["events"])
        else:
            assert full["events"][0][0] == 201 and full["events"][-1][0] == 213 and any(x[0] == 212 for x in full["events"])


def test_pump_points_stay_sorted_when_kicks_come_faster_than_the_release():
    from coproducer import pump

    pts = pump.pump_points([0.0, 1.0, 1.25, 1.5, 4.0], 5.0, -8.0)
    beats = [p[0] for p in pts]
    assert beats == sorted(beats) and len(set(beats)) == len(beats)
    low = min(p[1] for p in pts)
    assert all(p[1] == low for p in pts if 1.0 <= p[0] <= 1.6)
    assert pts[-1] == (5.0, pump.db_to_fader(0.0))
