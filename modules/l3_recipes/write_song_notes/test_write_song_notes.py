import json

from coproducer.services import set_service

NOTES = {"title": "A Song", "artist": "A Singer", "form": ["intro", "verse", "chorus", "solo", "verse", "chorus"],
         "mood": {"feel": ["bittersweet"], "evidence": ["a breakup story told with a grin; major key, mid tempo"]},
         "favorites": [{"what": "the chorus sing-along", "use": "both choruses whole over the drops", "source": "https://example.org/a"}],
         "sources": ["https://example.org/a"]}


def _words(tmp_path):
    w = "the quick brown fox jumps over the lazy dog every single night".split()
    p = tmp_path / "words.json"
    p.write_text(json.dumps({"words": [{"word": x, "start": i, "end": i + 0.5} for i, x in enumerate(w)]}))
    return str(p)


def test_writes_valid_notes(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    r = rig.call("write_song_notes", out_file=str(tmp_path / "song_notes.json"), notes=NOTES, words_file=_words(tmp_path))
    assert r.ok and r.meta["verified"] and json.loads((tmp_path / "song_notes.json").read_text())["artist"] == "A Singer"


def test_refuses_lyrics_and_missing_fields(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    quoted = dict(NOTES, favorites=[{"what": "the line: The quick brown fox jumps over the lazy dog", "source": "https://example.org/a"}])
    assert rig.call("write_song_notes", out_file=str(tmp_path / "n.json"), notes=quoted, words_file=_words(tmp_path)).error.code == "E_ARG"
    assert rig.call("write_song_notes", out_file=str(tmp_path / "n.json"), notes={"title": "x"}).error.code == "E_ARG"
    assert rig.call("write_song_notes", out_file=str(tmp_path / "n.json"), notes=dict(NOTES, mood={"feel": ["sad"]})).error.code == "E_ARG"
    assert rig.call("write_song_notes", out_file="/elsewhere/n.json", notes=NOTES).error.code == "E_SANDBOX_VIOLATION"
