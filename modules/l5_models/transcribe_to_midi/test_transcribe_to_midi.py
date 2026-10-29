from coproducer.services import set_service
from coproducer.synth import sine, to_wav


def test_converts_seconds_to_beats(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = to_wav(str(tmp_path / "a.wav"), sine(440, 1.0))
    r = rig.call("transcribe_to_midi", input_path=src, tempo_bpm=120, out_midi_path=str(tmp_path / "t.mid"))
    assert r.ok and r.value["count"] == 2
    assert r.value["notes"][0] == {"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 102}      # 0.5 s at 120 bpm is 1 beat
    assert r.value["notes"][1]["start"] == 1.0 and r.value["notes"][1]["velocity"] == 76
    back = rig.call("read_midi_file", path=str(tmp_path / "t.mid")).value
    assert [n["pitch"] for n in back["notes"]] == [60, 64] and back["tempo_bpm"] == 120.0
    slow = rig.call("transcribe_to_midi", input_path=src, tempo_bpm=60).value["notes"]
    assert slow[0]["duration"] == 0.5


def test_missing_file(rig, ml, tmp_path):
    assert rig.call("transcribe_to_midi", input_path=str(tmp_path / "no.wav")).error.code == "E_NOT_FOUND"
    src = to_wav(str(tmp_path / "a.wav"), sine(440, 0.2))
    assert rig.call("transcribe_to_midi", input_path=src, out_midi_path=str(tmp_path / "outside.mid")).error.code == "E_SANDBOX_VIOLATION"
