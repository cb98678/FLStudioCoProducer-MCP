"""Level of a part at its own hits: band-limited RMS in a short window after each expected event. Run from the repo root.

    python tools/hit_meter.py RENDER.wav --bpm 140 --bars 35,39 --hit kick=0,8:40-120 --hit snare=4,12:150-4000 [--compare OTHER.wav]

--hit NAME=STEPS:LOW-HIGH where STEPS are sixteenth steps in the bar. With --compare the table shows OTHER minus RENDER.
Use it before and after a fader move: a heavy master limiter can hide a few dB, and this shows how much actually arrived.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import mixtools  # noqa: E402


def parse_hit(text: str) -> tuple[str, tuple[list[float], float, float]]:
    name, rest = text.split("=", 1)
    steps, band = rest.split(":")
    lo, hi = band.split("-")
    return name, ([float(s) for s in steps.split(",")], float(lo), float(hi))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("--bpm", type=float, default=140)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--hit", action="append", required=True)
    ap.add_argument("--compare")
    ap.add_argument("--shift-steps", type=float, default=0.0)
    a = ap.parse_args()
    bars = [int(b) for b in a.bars.split(",")]
    hits = dict(parse_hit(h) for h in a.hit)
    x, sr = sf.read(a.render)
    A = mixtools.hit_levels(x, sr, a.bpm, bars, hits, shift_steps=a.shift_steps)
    B = None
    if a.compare:
        y, sr2 = sf.read(a.compare)
        B = mixtools.hit_levels(y, sr2, a.bpm, bars, hits, shift_steps=a.shift_steps)
    for name in hits:
        for bar in bars:
            row = A[name][bar]
            line = "%-8s bar %3d  %s" % (name, bar, " ".join("%6.1f" % v for v in row))
            if B:
                line += "   delta " + " ".join("%+5.1f" % (b - v) for v, b in zip(row, B[name][bar]))
            print(line)
        mean = mixtools.mean_level(A[name])
        print("%-8s mean %.1f dB%s" % (name, mean, ("   delta %+.1f" % (mixtools.mean_level(B[name]) - mean)) if B else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
