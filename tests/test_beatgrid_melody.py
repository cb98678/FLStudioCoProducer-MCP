"""beatgrid and melody on the Friends stems as beat_this and torchcrepe saw them on the host (2026-10-25, tests/data/friends_beats_melody.json)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from coproducer import beatgrid, melody

DATA = json.loads((Path(__file__).parent / "data" / "friends_beats_melody.json").read_text())


def test_friends_grid_matches_the_hand_measurements():
    g = beatgrid.analyze(DATA["beats"]["beats"], DATA["beats"]["downbeats"])
    assert g["meter"] == 4 and g["odd_bars"] == [] and not g["drifting"]
    assert abs(g["bpm"] - 108.478) < 0.05            # found by hand on 2026-10-23
    k = beatgrid.first_bar_after(g, 27.3085)          # the hand-found first drum hit
    assert abs(g["bars"][k] - 27.3085) < 0.04
    assert abs(beatgrid.bar_to_time(g, beatgrid.time_to_bar(g, 100.0)) - 100.0) < 1e-6


def test_grid_reports_drift_and_odd_bars():
    beats = [i * 0.5 for i in range(64)]
    slow = [32 * 0.5 + i * 0.56 for i in range(1, 33)]  # the second half drags by 12 %
    g = beatgrid.analyze(beats[:33] + slow, (beats[:33] + slow)[::4])
    assert g["drifting"] and g["max_drift_pct"] > 3
    waltz = [i * 0.5 for i in range(48)]
    assert beatgrid.analyze(waltz, waltz[::3])["meter"] == 3
    with pytest.raises(ValueError):
        beatgrid.analyze([0, 1], [0])


def test_friends_chorus_notes():
    m = DATA["melody"]
    notes = melody.notes_from_f0(m["f0"], m["periodicity"], m["rms"], m["hop_s"], m["offset_s"])
    assert 30 <= len(notes) <= 60
    assert all(45 <= n["pitch"] <= 66 for n in notes)      # a baritone, about A2 to F#4
    assert all(n["end"] > n["start"] >= 130 for n in notes)
    key = melody.key_from_notes(notes)
    assert {key["name"], key["runner_up"]} & {"A major", "E major"}


def test_similarity_ignores_transposition_and_sees_a_different_tune():
    a = [{"start": i * 0.3, "end": i * 0.3 + 0.28, "pitch": p, "velocity": 90} for i, p in enumerate([60, 62, 64, 65, 67, 65, 64, 62])]
    up = [{**n, "pitch": n["pitch"] + 7} for n in a]
    other = [{**n, "pitch": p} for n, p in zip(a, [60, 60, 67, 67, 69, 69, 67, 67])]
    assert melody.contour_similarity(a, up) > 0.9 and melody.contour_similarity(a, other) < 0.6


def test_tempo_from_downbeats_when_the_beats_wander_and_grid_fit():
    from coproducer import beatgrid
    bar = 240 / 174
    downs = [i * bar for i in range(40)]
    beats = []
    for i, d in enumerate(downs):                                                    # a syncopated render: the tracker doubles some bars
        n = 8 if i % 5 == 2 else 4
        beats += [d + k * bar / n for k in range(n)]
    g = beatgrid.analyze(beats, downs)
    assert g["tempo_from"] == "downbeats" and abs(g["bpm"] - 174) < 0.05 and g["steady"]
    fit = beatgrid.grid_fit(downs, bar)
    assert fit["share"] == 1.0 and fit["median_ms"] < 1
    off = beatgrid.grid_fit([t + (0.2 if i % 3 == 0 else 0) for i, t in enumerate(downs)], bar)
    assert 0.6 < off["share"] < 0.7                                                  # a third of the events off the grid
    assert beatgrid.grid_fit(downs, 240 / 150)["share"] < 0.3                        # a wrong tempo does not fit


def test_rendered_remixes_read_their_style_tempo():
    """beat_this on three host renders (2026-10-25): counting gaps read 124.2, 142.9 and 190.8; numbering by the grid reads the project tempo."""
    import json
    from pathlib import Path

    from coproducer import beatgrid
    data = json.loads((Path(__file__).parent / "data" / "render_beats.json").read_text())
    for bpm, d in data.items():
        g = beatgrid.analyze(d["beats"], d["downbeats"])
        assert abs(g["bpm"] - float(bpm)) < 0.1, (bpm, g["bpm"])
        assert max(beatgrid.grid_fit(d["beats"], 60 / float(bpm))["share"], beatgrid.grid_fit(d["downbeats"], 240 / float(bpm))["share"]) >= 0.8
