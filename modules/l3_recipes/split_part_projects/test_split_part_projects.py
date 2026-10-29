import json

from coproducer import flpfile
from coproducer.testflp import project


def test_splits_by_track(rig, desk, tmp_path):
    f = project({0: "Kick", 1: "Chord Stab"}, {0: [0], 1: [0]})
    f.set_track(0, 1)
    f.set_track(1, 2)
    src = tmp_path / "mix.flp"
    f.save(str(src))
    before = src.read_bytes()
    r = rig.call("split_part_projects", project=str(src), out_dir=str(tmp_path / "sandbox" / "solo"))
    assert r.ok and r.meta["verified"] and r.value["projects"] == 2
    man = json.loads((tmp_path / "sandbox" / "solo" / "manifest.json").read_text())
    assert {m["role"] for m in man["tracks"].values()} == {"kick", "stab"}
    for m in man["tracks"].values():
        g = flpfile.Flp.load(str(tmp_path / "sandbox" / "solo" / (m["name"] + ".flp")))
        assert [g.channel_info(c)["name"] for c in g.channel_ids() if g.channel_info(c)["enabled"]] == m["channels"]
    assert src.read_bytes() == before


def test_failures(rig, desk, tmp_path):
    assert rig.call("split_part_projects", project=str(tmp_path / "mix.flp"), out_dir="/elsewhere/solo").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("split_part_projects", project=str(tmp_path / "no.flp"), out_dir=str(tmp_path / "sandbox" / "solo")).error.code == "E_IO"
    assert rig.call("split_part_projects", project="", out_dir="x").error.code == "E_ARG"
