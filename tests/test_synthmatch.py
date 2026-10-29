import numpy as np

from coproducer import oneshots as O
from coproducer import synthmatch as S


def note(hz, harm=(0.22, 0.08), decay=0.6, seconds=1.5):
    x = O.sub_sine(hz, seconds, harm)
    return x * np.exp(-np.arange(len(x)) / O.SR / decay)


def test_describe_finds_fundamental_and_harmonics():
    d = S.describe_tone(note(43.65), O.SR)
    assert abs(d["fundamental_hz"] - 43.65) < 1.0 and -16 < d["h2_db"] < -10 and d["decay_s"] > 0.5


def test_same_note_matches():
    t = S.describe_tone(note(43.65), O.SR)
    r = S.compare_tones(t, S.describe_tone(note(43.65), O.SR))
    assert r["match"] and r["adjust"] == []


def test_detuned_brighter_shorter_note_gets_advice():
    t = S.describe_tone(note(43.65), O.SR)
    c = S.describe_tone(note(55.0, harm=(0.9, 0.7), decay=0.15), O.SR)
    r = S.compare_tones(t, c)
    assert not r["match"] and any("cents" in s for s in r["adjust"]) and any("harmonics" in s for s in r["adjust"]) and any("decay" in s for s in r["adjust"])
