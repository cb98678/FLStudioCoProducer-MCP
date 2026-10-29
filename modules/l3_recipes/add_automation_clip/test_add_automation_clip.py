from coproducer import automation as A
from coproducer.flpfile import Flp
from coproducer.services import set_service
from coproducer.testrig import synthetic_flp


def _box(tmp_path):
    box = tmp_path / "box"
    (box / "p").mkdir(parents=True)
    set_service("sandbox_root", str(box))
    f = synthetic_flp()
    f.save(box / "p" / "a.flp")
    return box / "p" / "a.flp"


def test_adds_clip_and_reads_it_back(rig, tmp_path):
    p = _box(tmp_path)
    r = rig.call("add_automation_clip", project=str(p), name="Vocal duck", target={"kind": "track_volume", "track": 3},
                 curve={"duck": {"length": 16, "windows": [[4, 6]], "normal": 0, "low": -12}}, unit="db")
    assert r.ok and r.meta["verified"] and r.value["link"] == "0x70c01fc0" and r.value["playlist_track"] == 1
    [c] = A.list_automation(Flp.load(p))
    assert c["name"] == "Vocal duck" and abs(c["points"][0][1] - 0.8) < 1e-6 and abs(c["points"][3][1] - A.db_to_fader(-12)) < 1e-6
    assert (p.parent / "a.pre_automation.flp").exists()
    r2 = rig.call("add_automation_clip", project=str(p), name="Pan", target={"kind": "track_pan", "track": 3},
                  curve={"ramp": {"length": 8, "from": 0.5, "to": 0.2}}, playlist_track=4)
    assert r2.ok and r2.value["channel"] == r.value["channel"] + 1 and len(A.list_automation(Flp.load(p))) == 2


def test_refuses_bad_input(rig, tmp_path):
    p = _box(tmp_path)
    ok_curve = {"ramp": {"length": 4, "from": 0.1, "to": 0.9}}
    assert rig.call("add_automation_clip", project=str(p.parent / "no.flp"), name="x", target={"kind": "track_pan", "track": 1}, curve=ok_curve).error.code == "E_NOT_FOUND"
    outside = tmp_path / "out.flp"
    synthetic_flp().save(outside)
    assert rig.call("add_automation_clip", project=str(outside), name="x", target={"kind": "track_pan", "track": 1}, curve=ok_curve).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("add_automation_clip", project=str(p), name="x", target={"kind": "plugin_param", "track": 1, "param": 9000, "slot": 2}, curve=ok_curve).error.code == "E_ARG"
    assert rig.call("add_automation_clip", project=str(p), name="x", target={"kind": "track_pan", "track": 1}, curve={"ramp": {"length": 4, "from": 0.1, "to": 1.9}}).error.code == "E_ARG"
    assert rig.call("add_automation_clip", project=str(p), name="x", target={}, curve=ok_curve).error.code == "E_ARG"
    assert rig.call("add_automation_clip", project=str(p), name="x", target={"kind": "track_pan", "track": 1}, curve={}).error.code == "E_ARG"
    before = p.read_bytes()
    assert rig.call("add_automation_clip", project=str(p), name="x", target={"kind": "track_pan", "track": 1}, curve={"points": [{"beat": 1, "value": 0.5}, {"beat": 2, "value": 0.5}]}).error.code == "E_ARG"
    assert p.read_bytes() == before
