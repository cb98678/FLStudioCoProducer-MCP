import json


def test_clues_from_name_and_transcript(rig, tmp_path):
    song = tmp_path / "Some_Artist-Big_Song.mp3"
    song.write_bytes(b"not audio")
    words = ("i walk alone " + "under the bright night sky " * 4 + "and then i go").split()
    wf = tmp_path / "w.json"
    wf.write_text(json.dumps({"words": [{"word": w, "start": i, "end": i + 0.4} for i, w in enumerate(words)]}))
    r = rig.call("find_song_clues", input_path=str(song), words_file=str(wf))
    assert r.ok and r.value["file_name"] == "Some Artist Big Song"
    assert r.value["repeated_line"] in ("under the bright night sky", "bright night sky") and r.value["queries"]


def test_missing_file(rig, tmp_path):
    assert rig.call("find_song_clues", input_path=str(tmp_path / "none.mp3")).error.code == "E_NOT_FOUND"
