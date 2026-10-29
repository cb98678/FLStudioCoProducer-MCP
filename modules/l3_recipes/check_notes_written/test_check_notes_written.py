import json

NOTES = [{"pitch": 60, "start": 0, "duration": 1, "velocity": 100}, {"pitch": 64, "start": 1.5, "duration": 0.25}]
GOOD = {"expected": 2, "written": 2, "total": 2, "ppq": 96, "notes": [[60, 0, 96, 0.7874], [64, 144, 24, 0.7874]]}


def test_matching_counts_and_notes(rig, tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps(GOOD))
    r = rig.call("check_notes_written", result_path=str(f), expected=2)
    assert r.ok and r.meta["verified"] is True
    r = rig.call("check_notes_written", result_path=str(f), expected=2, notes=NOTES)
    assert r.ok and r.meta["verified"] is True


def test_missing_short_broken_and_wrong_notes(rig, tmp_path):
    f = tmp_path / "r.json"
    assert rig.call("check_notes_written", result_path=str(f), expected=2).error.code == "E_NOT_FOUND"
    f.write_text(json.dumps({"expected": 2, "written": 1}))
    assert rig.call("check_notes_written", result_path=str(f), expected=2).error.code == "E_NOT_VERIFIED"
    f.write_text("{oops")
    assert rig.call("check_notes_written", result_path=str(f), expected=2).error.code == "E_IO"
    wrong = dict(GOOD, notes=[[60, 0, 96, 0.7874], [65, 144, 24, 0.7874]])
    f.write_text(json.dumps(wrong))
    r = rig.call("check_notes_written", result_path=str(f), expected=2, notes=NOTES)
    assert r.error.code == "E_NOT_VERIFIED" and "differ" in r.error.message
