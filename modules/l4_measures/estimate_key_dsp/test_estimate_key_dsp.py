import numpy as np

from coproducer import dsp, synth


def _scale_audio(tonic, scale):
    base = dsp.NOTE_NAMES.index(tonic)
    w = {0: 3.0, 4: 1.5, 3: 1.5, 7: 2.0}
    x = 0
    for d in scale:
        f = 440.0 * 2 ** ((((base + d) % 12) - 9 - 12) / 12)
        x = x + w.get(d, 0.6) * synth.chord([f, 2 * f], 1.0, 22050)
    return x / np.max(np.abs(x))


def test_finds_the_key(rig, wav):
    minor = [0, 2, 3, 5, 7, 8, 10]
    r = rig.call("estimate_key_dsp", path=wav("a", _scale_audio("A", minor), 22050))
    assert r.ok and r.value["key"] == "A minor" and r.value["margin"] > 0.02
    major = [0, 2, 4, 5, 7, 9, 11]
    assert rig.call("estimate_key_dsp", path=wav("b", _scale_audio("D#", major), 22050)).value["key"] == "D# major"


def test_failures(rig, tmp_path):
    assert rig.call("estimate_key_dsp", path=str(tmp_path / "no.wav")).error.code == "E_IO"
    assert rig.call("estimate_key_dsp", path=3).error.code == "E_ARG"
