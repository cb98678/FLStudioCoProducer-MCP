from coproducer.services import set_service

NOTES = [{"pitch": 60, "start": 0, "duration": 1, "velocity": 90}, {"pitch": 64, "start": 0.5, "duration": 1.5},
         {"pitch": 36, "start": 2, "duration": 0.25, "channel": 9}]


def test_writes_and_rereads(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    (tmp_path / "out").mkdir()
    r = rig.call("write_midi_file", notes=NOTES, path=str(tmp_path / "out" / "a.mid"), tempo_bpm=150.0)
    assert r.ok and r.value["notes"] == 3
    back = rig.call("read_midi_file", path=r.value["path"]).value
    assert back["tempo_bpm"] == 150.0
    got = [(n["pitch"], n["start"], n["duration"], n["velocity"], n["channel"]) for n in back["notes"]]
    assert got == [(60, 0.0, 1.0, 90, 0), (64, 0.5, 1.5, 100, 0), (36, 2.0, 0.25, 100, 9)]


def test_sandbox_and_input_errors(rig, tmp_path):
    assert rig.call("write_midi_file", notes=NOTES, path=str(tmp_path / "a.mid")).error.code == "E_SANDBOX_VIOLATION"
    set_service("sandbox_root", str(tmp_path / "box"))
    (tmp_path / "box").mkdir()
    assert rig.call("write_midi_file", notes=NOTES, path=str(tmp_path / "outside.mid")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("write_midi_file", notes=NOTES, path=str(tmp_path / "box" / ".." / "x.mid")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("write_midi_file", notes=[{"pitch": 300, "start": 0, "duration": 1}], path="x").error.code == "E_ARG"
