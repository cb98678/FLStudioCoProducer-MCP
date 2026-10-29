import numpy as np

from coproducer import vocalchops as V

RATE = 44100


def _burst(secs, f=300.0, amp=0.4):
    t = np.arange(int(secs * RATE)) / RATE
    return amp * np.sin(2 * np.pi * f * t) * np.hanning(len(t)) ** 0.3


def test_phrases_split_on_gaps_and_ignore_blips():
    x = np.concatenate([np.zeros(RATE // 2), _burst(1.0), np.zeros(RATE), _burst(0.8), np.zeros(RATE // 5), _burst(0.05), np.zeros(RATE)])
    ph = V.phrases(x, RATE)
    assert len(ph) == 2
    assert abs(ph[0]["start"] - 0.5) < 0.05 and abs(ph[0]["end"] - 1.5) < 0.06
    assert abs(ph[1]["start"] - 2.5) < 0.05


def test_onsets_and_chops_inside_a_phrase():
    x = np.concatenate([np.zeros(RATE // 4)] + [np.concatenate([_burst(0.3), np.zeros(RATE // 20)]) for _ in range(4)] + [np.zeros(RATE // 4)])
    ph = V.phrases(x, RATE, min_gap=0.2)
    assert len(ph) == 1
    ons = V.onsets(x, RATE, ph[0]["start"], ph[0]["end"])
    assert 2 <= len(ons) <= 4
    ch = V.chop_candidates(x, RATE, ph)
    assert len(ch) >= 3 and all(0.12 <= c["end"] - c["start"] <= 0.7 for c in ch)


def test_silence_has_no_phrases():
    assert V.phrases(np.zeros(RATE), RATE) == []


def _held(secs, f=220.0, amp=0.4):
    t = np.arange(int(secs * RATE)) / RATE
    return amp * np.sin(2 * np.pi * f * t) * np.minimum(1.0, np.minimum(t / 0.02, (secs - t) / 0.05))


def _line():
    """quiet, word one (0.5 s), shallow dip, word two held 1.2 s, 0.4 s gap, word three 0.9 s, silence."""
    parts = [np.zeros(RATE // 2), _held(0.5), 0.4 * _held(0.12), _held(1.2, 330.0), np.zeros(int(0.4 * RATE)), _held(0.9, 262.0), np.zeros(RATE)]
    return np.concatenate(parts)


def test_gaps_find_the_silences_not_the_shallow_dip():
    x = _line()
    g = V.gaps(x, RATE)
    starts = [round(a, 1) for a, b in g]
    assert any(abs(a - 2.4) < 0.15 and 0.2 < b - a < 0.6 for a, b in g)
    assert not any(0.9 < a < 1.2 for a, b in g)  # the shallow dip between word one and two is not a gap
    assert starts[0] < 0.2  # leading silence


def test_phrase_end_runs_to_the_end_of_a_held_last_word_even_from_an_early_hint():
    x = _line()
    g = V.gaps(x, RATE)
    last_start = 0.5 + 0.5 + 0.12 + 1.2 + 0.4
    hint = last_start + 0.3  # a hint that falls inside the last word, well before it ends
    end = V.snap_end([], g, hint, "phrase")
    assert abs(end - (last_start + 0.9)) < 0.1


def test_word_end_stops_at_the_next_onset():
    ons = [1.0, 2.0]
    assert abs(V.snap_end(ons, [], 1.9, "word") - (2.0 - 0.02)) < 1e-6
    assert V.snap_end([], [], 1.9, "word") == 1.9


def test_start_snaps_to_an_onset_with_preroll():
    assert abs(V.snap_start([0.5, 1.0, 1.6], 1.1) - 0.98) < 1e-9
    assert V.snap_start([0.2], 3.0) == 3.0


def test_squeeze_gaps_shortens_a_long_silence_only():
    x = _line()
    g = [(2.5, 2.9), (0.0, 0.5)]
    y = V.squeeze_gaps(x, RATE, [(2.5, 2.9)], 0.2)
    assert abs((len(x) - len(y)) / RATE - 0.2) < 0.01
    assert V.squeeze_gaps(x, RATE, [(2.5, 2.6)], 0.2).shape == x.shape
    assert g


def test_cut_report_flags_a_cut_made_mid_note():
    x = _line()
    inside = V.cut_report(x, RATE, 0.5, 2.0)
    clean = V.cut_report(x, RATE, 0.5, 3.0)
    assert inside["ok"] is False or inside["end_rel_db"] > clean["end_rel_db"]
