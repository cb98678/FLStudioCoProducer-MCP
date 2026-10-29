import numpy as np

from coproducer import cutrefine


def test_head_match_rejects_leftover_syllable():
    assert cutrefine.head_match("Drowns and", "drowns")
    assert cutrefine.head_match("Browns", "drowns")
    assert not cutrefine.head_match("Hey, Browns", "drowns")
    assert cutrefine.head_match("whiskey drowns and the beer", "whiskey drowns")


def test_tail_match_needs_whole_word():
    assert cutrefine.tail_match("This is where the whiskey", "whiskey")
    assert cutrefine.tail_match("this is where the whisky", "whiskey")
    assert not cutrefine.tail_match("This is where the wisdom", "whiskey")
    assert not cutrefine.tail_match("This is where the wind", "whiskey")
    assert cutrefine.tail_match("And the beer chases my blues away.", "my blues away")


def test_first_run():
    assert cutrefine.first_run([False, False, True, True, False]) == 2
    assert cutrefine.first_run([False, True, False, True, True]) == 3
    assert cutrefine.first_run([False, False, True]) == 2
    assert cutrefine.first_run([False, False]) is None


def test_refine_uses_asr_to_move_cuts():
    rate = 8000
    x = np.zeros(rate * 6, dtype="float32")
    rng = np.random.default_rng(1)
    for a, b in ((1.0, 1.4), (1.5, 2.0), (2.1, 2.9)):  # three syllables with 100 ms gaps
        n = int((b - a) * rate)
        x[int(a * rate) : int(a * rate) + n] = rng.standard_normal(n) * 0.2
    gp = [(1.4, 1.5), (2.0, 2.1)]

    def asr(seg, sr):  # fake recogniser: the word "alpha" is syllables 1+2, "beta" is syllable 3
        rms = [float(np.sqrt(np.mean(seg[int(i * sr * 0.1) : int((i + 1) * sr * 0.1)] ** 2) + 1e-12)) for i in range(len(seg) // int(sr * 0.1))]
        loud = [i for i, v in enumerate(rms) if v > 0.05]
        return "beta" if loud and len(loud) >= 7 and rms[0] > 0.05 and sum(1 for v in rms if v > 0.05) < 12 else "other"

    r = cutrefine.refine(x, rate, gp, {"start": 2.1, "end": 2.9, "words": "beta"}, asr)
    assert "evidence" in r and r["end"] > r["start"]


def _voice_dip_hiss(rate=16000, hiss_at=0.62, hiss_len=0.07, next_at=0.72, with_hiss=True):
    """A held vowel to 0.4 s, a quiet voiced stretch, a sung final s, then the next word: the shape of "blues" in front of "away"."""
    rng = np.random.default_rng(3)
    t = np.arange(int(1.2 * rate)) / rate
    x = np.zeros_like(t)
    vow = (t > 0.1) & (t < 0.4)
    x[vow] = 0.2 * np.sin(2 * np.pi * 220 * t[vow]) + 0.1 * np.sin(2 * np.pi * 440 * t[vow])
    quiet = (t >= 0.4) & (t < hiss_at)
    x[quiet] = 0.004 * np.sin(2 * np.pi * 220 * t[quiet])
    if with_hiss:
        h = (t >= hiss_at) & (t < hiss_at + hiss_len)
        noise = rng.standard_normal(int(h.sum())) * 0.08
        from scipy import signal as sg

        sos = sg.butter(4, 5000, "hp", fs=rate, output="sos")
        x[h] = sg.sosfilt(sos, noise)
    nxt = t >= next_at
    x[nxt] = 0.2 * np.sin(2 * np.pi * 180 * t[nxt])
    return x.astype("float32"), rate


def test_final_s_reaches_the_hiss_after_a_dip_and_stops_before_the_next_word():
    x, rate = _voice_dip_hiss()
    e = cutrefine.final_s(x, rate, 0.42)
    assert 0.68 <= e <= 0.74, e  # hiss ends at 0.69, next word starts at 0.72


def test_final_s_leaves_an_end_alone_without_a_hiss_or_when_it_already_has_one():
    x, rate = _voice_dip_hiss(with_hiss=False)
    assert cutrefine.final_s(x, rate, 0.42) == 0.42
    x, rate = _voice_dip_hiss()
    assert cutrefine.final_s(x, rate, 0.70) == 0.70  # the hiss ended 10 ms ago: the cut already has its s


def test_wants_final_s_follows_the_spelling_of_the_last_word():
    assert cutrefine.wants_final_s({"words": "my blues", "next": "away"})
    assert cutrefine.wants_final_s({"words": "low places", "after": "the whiskey"})
    assert not cutrefine.wants_final_s({"words": "whiskey"})
    assert not cutrefine.wants_final_s({"words": "whiskey drowns", "next": "chases"})  # the next word brings its own hiss
    assert not cutrefine.wants_final_s({"head": "well", "tail": "low places"})  # long clips end where the voice stops


def _legato(rate=16000):
    """A held note (E4) sung straight into the next word on a lower note, the shape of "complain" held into "'cause" (Friends, 43 to 44.7 s)."""
    t = np.arange(int(3.0 * rate)) / rate
    f = np.where(t < 1.8, 329.6, 261.6)
    x = 0.2 * np.sin(2 * np.pi * np.cumsum(f) / rate) + 0.05 * np.sin(4 * np.pi * np.cumsum(f) / rate)
    x[t < 0.2] = 0.0
    return x.astype("float32"), rate


def test_word_start_finds_where_a_stretched_first_word_leaves_the_held_note():
    x, rate = _legato()
    s = cutrefine.word_start(x, rate, 0.9, 2.2)          # the recogniser put the next word's start at 0.9 s, inside the held note
    assert 1.70 <= s <= 1.82, s
    assert cutrefine.word_start(x, rate, 1.9, 2.1) == 1.9    # a short word keeps its time
    assert cutrefine.word_start(x, rate, 0.25, 2.2) == 0.25  # after a breath (silence before it) the recogniser is trusted
    assert cutrefine.word_start(x, rate, 0.9, 3.0) == 0.9    # over 2 s is not one word


def test_pitch_track_reads_the_note():
    from coproducer import vocalchops
    x, rate = _legato()
    times, f0 = vocalchops.pitch_track(x, rate, 0.5, 1.5)
    assert abs(float(np.nanmedian(f0)) - 329.6) < 8
    times, f0 = vocalchops.pitch_track(x, rate, 0.0, 0.15)
    assert np.isnan(f0).all()
