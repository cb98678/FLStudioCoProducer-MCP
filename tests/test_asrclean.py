"""asrclean: Whisper's repetition loops found and spliced (numbers from the Girlish Type Men transcript, 2026-10-29)."""
from coproducer import asrclean


def _w(word, t, d=0.3):
    return {"word": word, "start": t, "end": t + d}


def test_a_word_repeated_past_the_limit_is_a_loop_and_a_real_chant_is_not():
    real = [_w("go", 1.0 + 0.4 * i) for i in range(6)]          # a six-times chant stays
    loop = [_w("wing", 10.0 + 0.2 * i, 0.1) for i in range(40)]
    assert asrclean.loop_spans(real) == []
    spans = asrclean.loop_spans(real + loop)
    assert len(spans) == 1 and spans[0][0] == 10.0 and spans[0][1] >= 17.8


def test_hundreds_of_tiny_words_are_a_loop():
    syl = ["ka", "lo", "mi", "nu", "pe", "ra", "so", "ti", "vu"]
    tiny = [_w(syl[i % 9], 30.0 + 0.067 * i, 0.08) for i in range(100)]   # no word repeats in a row: only their length gives them away
    spans = asrclean.loop_spans(tiny)
    assert spans and spans[0][0] == 30.0


def test_windows_follow_the_phrases_and_stay_short():
    phrases = [{"start": 9.5, "end": 14.0}, {"start": 14.5, "end": 30.0}, {"start": 40.0, "end": 41.0}]
    w = asrclean.windows([(10.0, 35.0)], phrases)
    assert w[0][0] == 9.85 and all(b - a <= asrclean.WINDOW_MAX_S + 2 * asrclean.MARGIN_S + 1e-9 for a, b in w)
    assert w[-1][1] <= 30.15 + 1e-9                                 # nothing past the last phrase inside the span


def test_splice_keeps_the_good_words_and_drops_a_redo_that_loops_again():
    good = [_w("hello", 1.0), _w("there", 1.5)]
    loop = [_w("wing", 10.0 + 0.2 * i, 0.1) for i in range(40)]
    spans = asrclean.loop_spans(good + loop)
    redo_ok = [_w("real", 10.5), _w("words", 11.0)]
    out, rep = asrclean.splice(good + loop, spans, redo_ok)
    assert [x["word"] for x in out] == ["hello", "there", "real", "words"] and rep["removed"] == 40 and rep["redone"] == 2
    out2, rep2 = asrclean.splice(good + loop, spans, [_w("la", 10.0 + 0.2 * i, 0.1) for i in range(30)])
    assert [x["word"] for x in out2] == ["hello", "there"] and rep2["seconds_without_words"] > 0


def test_a_loop_is_judged_inside_its_own_window():
    syl = ["ka", "lo", "mi", "nu", "pe"]
    a = [_w(syl[i % 5], 10.0 + 0.1 * i, 0.08) for i in range(12)]     # twelve tiny words in one window
    b = [_w(syl[i % 5], 40.0 + 0.1 * i, 0.08) for i in range(12)]     # twelve more after a long gap
    spans = [(9.0, 12.0), (39.0, 42.0)]
    _out, rep = asrclean.splice([], spans, a + b)
    assert rep["still_looping"] == []                                     # neither window alone reaches the 20-word stretch
