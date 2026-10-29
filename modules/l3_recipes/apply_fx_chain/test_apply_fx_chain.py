import sys
from pathlib import Path

from coproducer import fxchains, fxlib
from coproducer import flpfile as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "l3_recipes" / "create_bus_routing"))
from test_create_bus_routing import project  # noqa: E402


def test_chains_by_role(rig, desk, tmp_path):
    src = project(tmp_path)
    bus = tmp_path / "sandbox" / "music.flp"
    assert rig.call("create_bus_routing", project=str(src), out_project=str(bus), name="Music Bus").ok
    out = tmp_path / "sandbox" / "chains.flp"
    r = rig.call("apply_fx_chain", project=str(bus), out_project=str(out))
    assert r.ok and r.meta["verified"] is True
    got = {d["insert"]: (d["chain"], [p["plugin"] for p in d["placed"]]) for d in r.value["applied"]}
    assert got[1] == ("kick", ["Fruity Parametric EQ 2", "Fruity Multiband Compressor"])
    assert got[2][0] == "stab" and got[3][0] == "sub" and got[4][0] == "chops" and len(got[4][1]) == 7
    assert got[6] == ("music_bus", ["Fruity Filter", "Fruity Reeverb 2"])
    g = F.Flp.load(str(out))
    assert fxlib.slot_plugin(g, 6, 0) == "Fruity Filter" and fxlib.slot_plugin(g, 5, 0) is None  # the Vocals Bus has no chain


def test_every_chain_names_library_entries():
    data = fxchains.load()
    for name in data["chains"]:
        c = fxchains.chain(name, data)
        for e in c["entries"]:
            entry = fxlib.load_entry(e)
            assert entry["plugin"] not in ("Fruity Love Philter", "Gross Beat", "Fruity Balance", "Edison", "Wave Candy"), (name, e)
    assert "\u2014" not in fxchains.CHAINS.read_text(encoding="utf-8")


def test_failures(rig, desk, tmp_path):
    src = str(project(tmp_path))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("apply_fx_chain", project=src, out_project=out, chains=[{"insert": 1, "chain": "polka"}]).error.code == "E_ARG"
    assert rig.call("apply_fx_chain", project=src, out_project="/elsewhere/x.flp").error.code == "E_SANDBOX_VIOLATION"
