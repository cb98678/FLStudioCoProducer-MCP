import json
import struct

from coproducer import flpfile as F
from coproducer import testflp


def _project(tmp_path):
    f = testflp.project({0: "Kick", 1: "Clip"}, {0: [0]}, bars=1)
    clip = f._starts()[1]
    f.events[clip + 1 : clip + 1] = [[21, b"\x05"]]  # an automation clip with no link event: an orphan
    f.events += [[149, bytes(4)], [42, b"\x01"], [236, bytes(12)], [201, F.enc16("Edison")], [212, struct.pack("<II", 0, 2) + bytes(44)],
                 [213, b"\x00"], [98, b"\x02\x00"], [235, b"\x00"], [147, bytes(4)]]
    p = tmp_path / "p.flp"
    f.save(str(p))
    snap = {"inserts": [{"index": 0, "slots": [{"slot": 3, "plugin": "Fruity Limiter", "params": {"2": {"name": "Limiter ceiling", "text": "4.0dB"}}}]}]}
    s = tmp_path / "snap.json"
    s.write_text(json.dumps(snap))
    return str(p), str(s)


def test_flags_orphans_meters_and_hot_master(rig, tmp_path):
    p, s = _project(tmp_path)
    r = rig.call("check_project_health", project=p, params_file=s, not_owned=["Edison"]).value
    kinds = {x["kind"] for x in r["items"]}
    assert {"orphan_automation", "meter_in_chain", "not_owned", "master_over_zero"} <= kinds
    assert r["render_safe"] is False and r["problems"] >= 3
    plain = rig.call("check_project_health", project=p).value
    assert "master_unchecked" in {x["kind"] for x in plain["items"]} and plain["render_safe"] is True


def test_failures(rig, tmp_path):
    assert rig.call("check_project_health", project=str(tmp_path / "none.flp")).error.code == "E_IO"
    p, _s = _project(tmp_path)
    assert rig.call("check_project_health", project=p, params_file=str(tmp_path / "none.json")).error.code == "E_IO"
