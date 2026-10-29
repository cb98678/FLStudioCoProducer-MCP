import mido


def make(path, tempo=140.0):
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo)))
    tr.append(mido.MetaMessage("time_signature", numerator=3, denominator=4))
    tr.append(mido.Message("note_on", note=60, velocity=100, time=0))
    tr.append(mido.Message("note_on", note=64, velocity=80, time=240))
    tr.append(mido.Message("note_off", note=60, velocity=0, time=240))
    tr.append(mido.Message("note_on", note=67, velocity=0, time=480))       # note_on with velocity 0 ends a note
    tr.append(mido.Message("note_off", note=64, time=0))
    mid.tracks.append(tr)
    mid.save(path)
    return str(path)


def test_reads_notes_tempo_and_signature(rig, tmp_path):
    r = rig.call("read_midi_file", path=make(tmp_path / "a.mid"))
    assert r.ok and r.value["ppq"] == 480 and r.value["tempo_bpm"] == 140.0 and r.value["time_signature"] == [3, 4]
    assert [(n["pitch"], n["start"], n["duration"], n["velocity"]) for n in r.value["notes"]] == [(60, 0.0, 1.0, 100), (64, 0.5, 1.5, 80)]
    assert r.value["length_beats"] == 2.0


def test_missing_and_garbage_files(rig, tmp_path):
    assert rig.call("read_midi_file", path=str(tmp_path / "no.mid")).error.code == "E_IO"
    bad = tmp_path / "bad.mid"
    bad.write_bytes(b"not midi at all")
    assert rig.call("read_midi_file", path=str(bad)).error.code == "E_IO"
