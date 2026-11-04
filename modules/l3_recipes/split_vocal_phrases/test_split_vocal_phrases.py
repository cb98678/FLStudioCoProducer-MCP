import json

import numpy as np
import soundfile as sf

from coproducer import vocalchunk
from coproducer.services import set_service

RATE = 48000
BPM = 120.0


RNG = np.random.default_rng(7)


def _burst(x, t, dur, f=220.0, level=0.3):
    """A sung syllable: a tone with breath noise, a 5 ms attack, held to its end."""
    i, n = int(t * RATE), int(dur * RATE)
    env = np.minimum(1.0, np.arange(n) / (0.005 * RATE)) * np.exp(-np.arange(n) / (0.6 * RATE))
    x[i:i + n] += level * env * (np.sin(2 * np.pi * f * np.arange(n) / RATE) + 0.3 * RNG.standard_normal(n))


def _song():
    """Three phrases on a 120 bpm grid (beat 0.5 s, 16th 0.125 s): syllables 20 ms early; "against" with an 80 ms closure inside it."""
    x = np.zeros(int(RATE * 9.0))
    beat = 0.5
    words = []
    # phrase 1: beats 2..3.75 ("for get the things")
    for k, w in enumerate(["for", "get", "the", "things"]):
        t = 2 * beat + k * 0.25 * beat * 2 - 0.02
        _burst(x, t, 0.2)
        words.append({"word": w, "start": round(t, 3), "end": round(t + 0.2, 3)})
    # phrase 2 at beat 6: "a" then an 80 ms closure then "gainst", then "me"
    t = 6 * beat - 0.02
    _burst(x, t, 0.15)
    _burst(x, t + 0.23, 0.3)
    words.append({"word": "against", "start": round(t, 3), "end": round(t + 0.53, 3)})
    _burst(x, t + 0.75, 0.3)
    words.append({"word": "me", "start": round(t + 0.75, 3), "end": round(t + 1.05, 3)})
    # phrase 3 at beat 11.5 (a half beat: the gap holds a beat line at 11.0 only if far enough)
    t = 11.5 * beat - 0.02
    for k, w in enumerate(["did", "you", "ex", "pect"]):
        _burst(x, t + k * 0.25, 0.18)
        words.append({"word": w, "start": round(t + k * 0.25, 3), "end": round(t + k * 0.25 + 0.18, 3)})
    return x, words


def test_cuts_phrases_in_their_silences_on_grid_lines(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    x, words = _song()
    src = tmp_path / "voice.wav"
    sf.write(str(src), np.stack([x, x], axis=1), RATE)
    (tmp_path / "words.json").write_text(json.dumps({"words": words}), encoding="utf-8")
    r = rig.call("split_vocal_phrases", path=str(src), out_dir=str(tmp_path / "chunks"), bpm=BPM, origin_s=0.0, words_path=str(tmp_path / "words.json"))
    assert r.ok, r
    man = json.loads((tmp_path / "chunks" / "chunks.json").read_text(encoding="utf-8"))
    ch = man["chunks"]
    assert len(ch) == 3 and r.value["chunks"] == 3
    assert [c["text"] for c in ch] == ["for get the things", "against me", "did you ex pect"]
    # every file starts on a grid line, on a beat where the silence held one, and the cut sits in the silence before the first syllable
    assert all(c["on_beat"] for c in ch) and [c["beat"] for c in ch] == [1.0, 5.0, 11.0]
    assert 0.9 <= ch[0]["audio_s"] <= 0.99 and 2.9 <= ch[1]["audio_s"] <= 2.99 and 5.6 <= ch[2]["audio_s"] <= 5.74
    assert not any("long" in c["flags"] or "short" in c["flags"] for c in ch)
    # the closure inside "against" was not a cut, the onsets sit early and the lead found it
    assert 0.01 <= man["lead_s"] <= 0.05
    assert all(-60 <= o <= 0 for c in ch for o in c["offsets_ms"])   # the detector marks a burst about 12 ms before its attack
    # the files lay back onto the original clock
    y = vocalchunk.assemble([c["file"] for c in ch], [c["grid_s"] for c in ch], RATE, 9.0)
    v = slice(int(1.1 * RATE), int(8.5 * RATE))
    assert np.max(np.abs(y[v, 0] - x[v])) < 0.02
    assert r.value["words_placed"] == len(words)


def test_refuses_bad_input(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    x, _ = _song()
    src = tmp_path / "voice.wav"
    sf.write(str(src), x, RATE)
    assert rig.call("split_vocal_phrases", path=str(src), out_dir="/elsewhere", bpm=120.0).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("split_vocal_phrases", path=str(tmp_path / "none.wav"), out_dir=str(tmp_path / "c"), bpm=120.0).error.code == "E_IO"
    assert rig.call("split_vocal_phrases", path=str(src), out_dir=str(tmp_path / "c"), bpm=500.0).error.code in ("E_ARG", "E_SCHEMA")
    quiet = tmp_path / "quiet.wav"
    sf.write(str(quiet), np.zeros(RATE), RATE)
    assert rig.call("split_vocal_phrases", path=str(quiet), out_dir=str(tmp_path / "c"), bpm=120.0).error.code == "E_NOT_FOUND"
