import struct

from coproducer import flpfile as F
from coproducer import testflp


def _mixer(names: list, routes: dict, slots: dict) -> list:
    """Mixer section in FL 26's order: an insert's colour, flag and name, its flags event 236, its slots, then its routing 235 and output 147."""
    out = []
    for n, name in enumerate(names):
        out += [[149, bytes((90, 100, 110, 0))], [42, b"\x01"]] + ([[204, F.enc16(name)]] if name else [])
        out.append([236, bytes(12)])
        for slot, plug in slots.get(n, {}).items():
            out += [[201, F.enc16(plug)], [212, struct.pack("<II", n, slot) + bytes(44)], [213, b"\x00"], [98, struct.pack("<H", slot)]]
        out += [[235, routes.get(n, b"\x01")], [147, b"\xff\xff\xff\xff"]]
    return out


def _project(tmp_path):
    f = testflp.project({0: "KICK", 1: "Kick A", 2: "Kick B", 3: "Pump"}, {0: [0, 96]}, bars=2)
    ev = f.events
    layer = f._starts()[0]
    ev[layer + 1 : layer + 1] = [[21, b"\x03"], [94, struct.pack("<H", 1)], [94, struct.pack("<H", 2)]]
    pump = f._starts()[3]
    ev[pump + 1 : pump + 1] = [[21, b"\x02"], [201, F.enc16("Fruity Envelope Controller")]]
    link = struct.pack("<HHIIII", 0x8000, 3, 0, 0x70000000 | 3 << 22 | 2 << 16 | 0x8007, 8, 469)
    ev[f._starts()[0] : f._starts()[0]] = [[227, link]]
    # insert 2 sends to insert 3 only (FL 26 trims trailing zeros from the routing event)
    ev += _mixer([None, "Kick", "Drums", "Bus"], {2: b"\x00\x00\x00\x01"}, {3: {2: "Fruity Love Philter"}})
    p = tmp_path / "a.flp"
    f.save(str(p))
    return str(p)


def test_reads_layers_routes_and_links(rig, tmp_path):
    r = rig.call("read_project_anatomy", project=_project(tmp_path)).value
    kick = [c for c in r["channels"] if c["name"] == "KICK"][0]
    assert kick["type"] == "layer" and kick["children"] == [1, 2]
    assert [x["to"] for x in r["inserts"][2]["routes"]] == [3] and r["inserts"][2]["name"] == "Drums"
    ctl = r["automation"]["controllers"][0]
    assert ctl["source_plugin"] == "Fruity Envelope Controller" and ctl["target"] == {
        "kind": "plugin", "insert": 3, "insert_name": "Bus", "slot": 2, "plugin": "Fruity Love Philter", "param": 7}
    assert any("layer KICK triggers channels [1, 2]" in s for s in r["summary"])
    only = rig.call("read_project_anatomy", project=_project(tmp_path), include=["channels"]).value
    assert "inserts" not in only and "summary" in only


def test_failures(rig, tmp_path):
    assert rig.call("read_project_anatomy", project=str(tmp_path / "missing.flp")).error.code == "E_IO"
    assert rig.call("read_project_anatomy", project="").error.code == "E_ARG"
