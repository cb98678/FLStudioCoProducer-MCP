import struct

from coproducer import anatomy, flporg, fxlib, mixroute, testflp
from coproducer import flpfile as F

PARTS = {0: ("Kick", 1), 1: ("Snare", 2), 2: ("Sub Bass", 3), 3: ("Chord Stab", 4), 4: ("Chops", 5), 5: ("FX Bed", 6)}


def arrangement(tmp_path, markers=True):
    """Six role-named parts on inserts 1 to 6, two free inserts and FL's last one; an Intro, Build 1, Drop 1 and Break; the kick on every beat."""
    f = testflp.project({c: n for c, (n, _t) in PARTS.items()}, {0: [0, 96, 192, 288], 3: [48]}, bars=24,
                        samples={1: "C:\\kit\\snare.wav", 4: "C:\\kit\\chop.wav", 5: "C:\\kit\\fx.wav"})
    f = testflp.with_mixer(f, tracks=10)
    for c, (_n, t) in PARTS.items():
        f.set_track(c, t)
    for n in range(10):
        f.events += [[149, bytes(4)], [42, b"\x01"]] + ([[204, F.enc16(PARTS[n - 1][0])]] if 1 <= n <= 6 else []) + [[236, bytes(12)]]
        f.events += [[98, struct.pack("<H", s)] for s in range(10)]
        f.events += [[235, b"\x00" if n in (0, 9) else b"\x01"], [147, bytes(4)]]
    rec = b"".join(struct.pack("<IHHI", 0, 0x1F00, 0x7000 + 64 * n + s, 0) for n in range(10) for s in range(10))
    f.events[f._mixer_index()][1] = bytes(f.events[f._mixer_index()][1]) + rec
    if markers:
        for bar, name in ((1, "Intro"), (5, "Build 1"), (9, "Drop 1"), (17, "Break")):
            f.add_time_marker((bar - 1) * 384, name)
    p = tmp_path / "sandbox" / "arr.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_club_house_on_a_small_arrangement(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "produced.flp"
    r = rig.call("apply_production_recipe", project=str(arrangement(tmp_path)), out_project=str(out), key="A")
    assert r.ok and r.meta["verified"] is True
    steps = {s["step"]: s["ok"] for s in r.value["steps"]}
    assert steps["bus Music Bus"] and steps["pump"] and steps["filter_sweep at Drop 1"] and steps["pitch_rise at Drop 1"]
    assert steps["noise_riser at Drop 1"] and steps["noise_downlifter at Break"] and "lowpass_open at Build 1" not in steps  # Intro>Build has no move
    g = F.Flp.load(str(out))
    bus = next(t for t in range(1, 9) if flporg.insert_name(g, t) == "Music Bus")
    assert mixroute.routes(g, 4) == [bus] and mixroute.routes(g, 5) == [bus] and mixroute.routes(g, 3) == [0]  # stab and chops in, sub out
    slots = [fxlib.slot_name(g, bus, s) or fxlib.slot_plugin(g, bus, s) for s in range(10) if fxlib.slot_plugin(g, bus, s)]
    assert slots[:2] == ["Fruity Filter", "Fruity Reeverb 2"] and {"Pump", "Throw Reverb", "Gap Gain"} <= set(slots)
    rep = anatomy.read(g)
    names = {c["name"] for c in rep["automation"]["clips"]}
    assert {"Pump %d" % bus, "Pump 3", "Filter Sweep Drop 1", "Pitch Rise Drop 1", "Fade In Drop 1", "Gap Drop 1"} <= names
    assert not any(n.startswith("Section Gain") for n in names) and steps["section gains"] is False  # left for after the first render


def test_failures(rig, desk, tmp_path):
    src = str(arrangement(tmp_path, markers=False))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("apply_production_recipe", project=src, out_project=out).error.code == "E_ARG"  # no markers
    assert rig.call("apply_production_recipe", project=src, out_project=out, recipe="polka").error.code == "E_ARG"
    assert rig.call("apply_production_recipe", project=src, out_project="/elsewhere/x.flp").error.code == "E_SANDBOX_VIOLATION"


def test_the_demo_study_recipes_apply(rig, desk, tmp_path):
    """The genre recipes from the FL demo study (2026-10-28) each produce the small arrangement with every step done."""
    src = str(arrangement(tmp_path))
    for name in ("trance", "afro_house", "lofi", "cinematic", "latin_pop"):
        out = tmp_path / "sandbox" / ("%s.flp" % name)
        r = rig.call("apply_production_recipe", project=src, out_project=str(out), recipe=name, key="A")
        assert r.ok, (name, r.error)
        bad = [s for s in r.value["steps"] if not s["ok"] and s["step"] != "section gains"]
        assert all(s["step"] == "pump" for s in bad), (name, bad)        # the small arrangement has a sub but no bass part for a bass pump
        assert sum(1 for s in r.value["steps"] if s["ok"] and s["step"] != "pump") >= 3, name
