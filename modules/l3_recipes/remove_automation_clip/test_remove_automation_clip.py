from coproducer import automation as A
from coproducer.flpfile import Flp
from coproducer.services import set_service
from coproducer.testrig import synthetic_flp


def _project(tmp_path):
    box = tmp_path / "box"
    (box / "p").mkdir(parents=True)
    set_service("sandbox_root", str(box))
    f = synthetic_flp()
    A.add_automation_clip(f, 5, "one", A.mixer_link(1), [(0.0, 0.8), (4.0, 0.3)])
    A.add_automation_clip(f, 6, "two", A.mixer_link(2), [(0.0, 0.8), (4.0, 0.3)], track=2)
    p = box / "p" / "a.flp"
    f.save(p)
    return p


def test_removes_only_the_named_clip(rig, tmp_path):
    p = _project(tmp_path)
    r = rig.call("remove_automation_clip", project=str(p), channel=5)
    assert r.ok and r.meta["verified"] and r.value["remaining"] == [6]
    f = Flp.load(p)
    assert [c["channel"] for c in A.list_automation(f)] == [6] and f.channel_ids() == [0, 1, 6]
    assert (p.parent / "a.pre_automation.flp").exists()


def test_refuses_non_automation_channel(rig, tmp_path):
    p = _project(tmp_path)
    before = p.read_bytes()
    assert rig.call("remove_automation_clip", project=str(p), channel=1).error.code == "E_ARG"
    assert rig.call("remove_automation_clip", project=str(p.parent / "x.flp"), channel=5).error.code == "E_NOT_FOUND"
    out = tmp_path / "out.flp"
    synthetic_flp().save(out)
    assert rig.call("remove_automation_clip", project=str(out), channel=5).error.code == "E_SANDBOX_VIOLATION"
    assert p.read_bytes() == before
