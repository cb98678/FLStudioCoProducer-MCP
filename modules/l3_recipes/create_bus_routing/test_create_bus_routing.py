import struct

from coproducer import flpfile as F
from coproducer import mixroute, testflp


def project(tmp_path, free=2):
    """Kick, Chord Stab, Sub Bass and Chops on inserts 1 to 4, a Vocals Bus on 5 fed by the chops, `free` empty inserts, and FL's last insert."""
    f = testflp.with_mixer(testflp.project({0: "Kick", 1: "Chord Stab", 2: "Sub Bass", 3: "Chops"}, {0: [0]}, bars=1), tracks=7 + free)
    for ch in range(4):
        f.set_track(ch, ch + 1)
    names = {1: "Kick", 2: "Chord Stab", 3: "Sub Bass", 4: "Chops", 5: "Vocals Bus"}
    for n in range(6 + free + 1):
        f.events += [[149, bytes(4)], [42, b"\x01"]] + ([[204, F.enc16(names[n])]] if n in names else []) + [[236, bytes(12)]]
        f.events += [[98, struct.pack("<H", s)] for s in range(10)]
        route = b"" if n == 0 or n == 6 + free else (b"\x00" * 5 + b"\x01" if n == 4 else b"\x01")
        f.events += [[235, route or b"\x00"], [147, bytes(4)]]
    p = tmp_path / "sandbox" / "bus.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_music_bus_takes_parts_and_family_buses(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "music.flp"
    r = rig.call("create_bus_routing", project=str(project(tmp_path)), out_project=str(out), name="Music Bus")
    assert r.ok and r.meta["verified"] is True
    assert r.value["bus"] == 6 and r.value["parts"] == [2, 4] and r.value["routed"] == [2, 5]  # the chops go via their Vocals Bus
    g = F.Flp.load(str(out))
    assert mixroute.routes(g, 3) == [0] and mixroute.routes(g, 1) == [0] and mixroute.routes(g, 4) == [5]  # sub and kick untouched
    assert mixroute.free_inserts(g) == [7]
    d = rig.call("create_bus_routing", project=str(out), out_project=str(tmp_path / "sandbox" / "drums.flp"), name="Drum Bus", kind="drums")
    assert d.ok and d.value["bus"] == 7 and d.value["routed"] == [1]


def test_failures(rig, desk, tmp_path):
    src = str(project(tmp_path, free=0))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("create_bus_routing", project=src, out_project=out, name="Music Bus").error.code == "E_ARG"  # no free insert
    assert rig.call("create_bus_routing", project=src, out_project=out, name="X", kind="custom").error.code == "E_ARG"
    assert rig.call("create_bus_routing", project=src, out_project="/elsewhere/x.flp", name="X").error.code == "E_SANDBOX_VIOLATION"
