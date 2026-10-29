"""remixstudy (2026-10-28): the original's sung lines found in a remix (whole, cut down, chopped), the tempo change, the 8-bar energy."""
import numpy as np

from coproducer import remixstudy as R


def _toks(text_times):
    out = []
    for words, t0 in text_times:
        for k, w in enumerate(words.split()):
            out.append({"w": w, "t0": t0 + 0.3 * k, "t1": t0 + 0.3 * k + 0.25})
    return out


def _song(text_times, bpm):
    from coproducer import songform
    toks = _toks(text_times)
    return {"words": toks, "lines": songform.lines(toks), "bpm": bpm, "bars": [], "key": "A minor", "mix_key": "A minor", "title": "t", "song": ""}


def test_lines_are_found_whole_cut_down_and_chopped():
    orig = _song([("i keep running back to you", 0.0), ("every night under the city lights", 4.0), ("hold me now", 8.0)], 100.0)
    remix = _song([("every night under the city lights", 10.0), ("hold me", 14.0), ("hold me", 15.0), ("hold me", 16.0),
                   ("running back to you", 20.0), ("something entirely different here", 30.0)], 125.0)
    m = R.map_lines(orig, remix)
    how = {l["line"]: l["treatments"] for l in m["lines"]}
    assert how[1] == ["whole"] and how[2] == ["chopped"] and how[0] == ["cut down"]
    assert m["lines"][2]["uses"] == 3 and m["timeline"][-1]["treatment"] == "new or unmatched"


def test_tempo_change_names_double_half_and_the_stretch():
    assert R.tempo_change(64.0, 128.0)["kind"] == "double"
    assert R.tempo_change(130.0, 122.0)["kind"].startswith("same, vocal -6.2")
    assert R.tempo_change(87.0, 174.0)["vocal_stretch_pct"] == 0.0 and R.tempo_change(0.0, 120.0)["kind"] == "unknown"


def test_blocks_and_report():
    rate = 8000
    x = np.zeros((rate * 40, 2))
    x[rate * 20:] = 0.3 * np.sin(np.linspace(0, 2 * np.pi * 220 * 20, rate * 20))[:, None]
    blks = R.blocks(x, rate, [], 120.0, size=8)              # 16 s blocks at 120 bpm
    assert len(blks) == 3 and blks[-1]["lufs"] > blks[0]["lufs"] + 20
    orig = _song([("hold me now", 1.0)], 120.0)
    remix = _song([("hold me now", 22.0)], 120.0)
    m = R.map_lines(orig, remix)
    text = R.report(orig, remix, m, R.with_vocals(blks, m["timeline"]))
    assert "| 1 | hold me now |" in text and "For the reading" in text and "—" not in text
