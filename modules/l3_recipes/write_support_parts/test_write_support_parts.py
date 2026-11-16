import json

import numpy as np

from coproducer.services import set_service

RATE, BPM = 16000, 120.0
CHORDS = [{"bar": b + 1, "chord": c} for b, c in enumerate(["D", "A", "G", "A"] * 2)]
SECTIONS = [{"name": "verse", "bars": [0, 4], "cell": "halves"}, {"name": "chorus", "bars": [4, 8], "cell": "push"}]


def voice(bars=8):
    t = np.arange(int(bars * 2.0 * RATE)) / RATE                       # a bar is 2 s at 120 bpm
    return 0.3 * np.sin(2 * np.pi * 330 * t) * ((t % 2.0) < 1.1) * (1 + 0.5 * np.sin(2 * np.pi * 6 * t))


def test_parts_around_a_vocal_pass_their_check(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    out = tmp_path / "sandbox" / "arr" / "parts.json"
    r = rig.call("write_support_parts", vocal_path=wav("v", voice()), chords=CHORDS, bpm=BPM, bars=8, key_pc=2, sections=SECTIONS, out_path=str(out),
                 options={"answer_every": 1, "vocal_notes": [[b * 4.0, 2.0, 64, 90] for b in range(8)]})
    assert r.ok and r.meta["verified"], r
    v = r.value
    assert v["check"]["ok"] and v["counts"]["bass"] > 0 and v["counts"]["pad"] > 0 and v["counts"]["answer"] > 0
    d = json.loads(out.read_text())
    for s, dur, *_ in d["parts"]["answer"]:
        assert (s % 4) >= 2.0                                              # she sings the first half of every bar: answers sit in the second
    import mido
    assert len(mido.MidiFile(v["midi"]).tracks) == 1 + sum(1 for k in v["counts"] if v["counts"][k])


def test_failures(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    good = dict(chords=CHORDS, bpm=BPM, bars=8, key_pc=2, sections=SECTIONS)
    v = wav("v", voice())
    assert rig.call("write_support_parts", vocal_path=v, out_path=str(tmp_path / "out.json"), **good).error.code == "E_SANDBOX_VIOLATION"
    inside = str(tmp_path / "sandbox" / "p.json")
    bad = dict(good, sections=[{"bars": [0, 8], "cell": "funky"}])
    assert rig.call("write_support_parts", vocal_path=v, out_path=inside, **bad).error.code == "E_ARG"
    assert rig.call("write_support_parts", vocal_path=v, out_path=inside, **dict(good, chords=[{"bar": 1, "chord": "H7"}])).error.code == "E_ARG"
    assert rig.call("write_support_parts", vocal_path=str(tmp_path / "none.wav"), out_path=inside, **good).error.code == "E_IO"
