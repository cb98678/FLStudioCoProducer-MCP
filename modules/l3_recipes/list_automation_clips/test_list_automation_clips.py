from coproducer import automation as A
from coproducer.testrig import synthetic_flp


def _project(tmp_path):
    f = synthetic_flp()
    A.add_automation_clip(f, 5, "Vol dip", A.mixer_link(2), [(0.0, 0.8), (4.0, 0.3)])
    p = tmp_path / "a.flp"
    f.save(p)
    return p


def test_lists_clips_with_targets(rig, tmp_path):
    r = rig.call("list_automation_clips", project=str(_project(tmp_path)))
    assert r.ok and r.value["count"] == 1
    c = r.value["clips"][0]
    assert c["channel"] == 5 and c["name"] == "Vol dip" and c["target"] == {"track": 2, "sub": 0, "param": 0x1FC0}
    assert c["points"] == [{"beat": 0.0, "value": 0.8}, {"beat": 4.0, "value": 0.3}]


def test_missing_or_bad_file(rig, tmp_path):
    assert rig.call("list_automation_clips", project=str(tmp_path / "no.flp")).error.code == "E_NOT_FOUND"
    bad = tmp_path / "bad.flp"
    bad.write_bytes(b"not an flp")
    assert rig.call("list_automation_clips", project=str(bad)).error.code == "E_ARG"
