"""Detect drum hits in a drum stem and write the grid fit, counts, a typical bar and note rows.

    python tools/drum_hits.py DRUMS.wav OUT.json [--bpm 108] [--origin SECONDS]

OUT.json: bpm, offset_s, counts, typical_bar (16th steps per drum for the most repeated bar), notes {kind: [[start_beat, dur, key, vel]]}.
"""
import argparse
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import drumhits, dsp

KEYS = {"kick": 36, "snare": 38, "hat": 42}


def grid_error_ms(hits: list[dict], bpm: float, offset: float) -> float | None:
    """Mean distance of the hits from the nearest 16th line, in milliseconds."""
    if not hits:
        return None
    step = 60.0 / bpm / 4
    pos = (np.array([h["t"] for h in hits]) - offset) / step
    return round(float(np.mean(np.abs(pos - np.round(pos)))) * step * 1000, 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, default=0.0)
    ap.add_argument("--origin", type=float, default=None)
    a = ap.parse_args()
    x, rate = dsp.load_audio(a.wav)
    m = dsp.mono(x)
    guess = a.bpm or dsp.estimate_tempo(x, rate)[0]["bpm"]
    hits = drumhits.detect_hits(m, rate)
    bpm, offset = drumhits.fit_grid([h["t"] for h in hits], guess)
    rows = drumhits.to_note_rows(hits, bpm, offset, KEYS, origin=a.origin)
    bars: dict[int, dict[str, list[int]]] = {}
    for kind, items in rows.items():
        for start, _, _, _ in items:
            bars.setdefault(int(start // 4), {k: [] for k in KEYS})[kind].append(round(start % 4 * 4))
    sig = Counter(json.dumps(b, sort_keys=True) for b in bars.values())
    typical = json.loads(sig.most_common(1)[0][0]) if sig else {}
    out = {"file": os.path.basename(a.wav), "seconds": round(len(m) / rate, 2), "bpm_guess": guess, "bpm": round(bpm, 3),
           "offset_s": round(offset, 4), "origin_s": round(drumhits.beat_zero(hits, bpm, offset, origin=a.origin), 4), "counts": dict(Counter(h["kind"] for h in hits)), "bars": len(bars),
           "typical_bar": typical, "typical_bar_repeats": sig.most_common(1)[0][1] if sig else 0,
           "mean_abs_grid_error_ms": grid_error_ms(hits, bpm, offset),
           "hits": [[round(h["t"], 4), h["kind"], round(h["strength"], 3)] for h in hits], "notes": rows}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print({k: v for k, v in out.items() if k not in ("notes", "hits")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
