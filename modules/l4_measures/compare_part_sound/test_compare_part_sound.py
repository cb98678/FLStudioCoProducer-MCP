import numpy as np

RATE = 44100


def plucks(tau, f0=220.0, n=5):
    t = np.arange(int(0.8 * RATE)) / RATE
    note = 0.5 * sum(np.sin(2 * np.pi * k * f0 * t) / k for k in range(1, 25)) * np.minimum(1, t / 0.002) * np.exp(-t / tau)
    return np.concatenate([np.concatenate([note, np.zeros(int(0.2 * RATE))]) for _ in range(n)])


def test_a_longer_decay_is_named(rig, wav):
    same = rig.call("compare_part_sound", original=wav("a", plucks(0.15)), remake=wav("b", plucks(0.15))).value
    assert same["match"] and same["adjust"] == []
    long = rig.call("compare_part_sound", original=wav("a", plucks(0.15)), remake=wav("c", plucks(0.3))).value
    assert not long["match"] and long["differences"]["decay_ratio"] > 1.6 and any("shorten env0 decay" in x for x in long["adjust"])
    up = rig.call("compare_part_sound", original=wav("a", plucks(0.15)), remake=wav("d", plucks(0.15, f0=440.0))).value
    assert any("octave" in x for x in up["adjust"]) and abs(up["differences"]["register_semitones"] - 12) < 0.5


def test_failures(rig, wav, tmp_path):
    good = wav("a", plucks(0.15))
    assert rig.call("compare_part_sound", original=good, remake=str(tmp_path / "none.wav")).error.code == "E_IO"
    assert rig.call("compare_part_sound", original=good, remake=wav("z", np.zeros(RATE))).error.code == "E_NOT_FOUND"
