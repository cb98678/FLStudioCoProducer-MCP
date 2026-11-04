"""Move a transcript's word times onto a warped file's clock (tools/warp_to_grid.py writes OUT.map.json beside each output).

    python tools/warp_words.py --map sandbox/songs/NAME/warped/vocals_117.map.json --words sandbox/songs/NAME/vocal_words.json --out sandbox/songs/NAME/warped/vocal_words.json

Between two beats of the recording the warp is linear (one tempo), so each time moves by the same rule as the audio: beat k of the
recording to grid beat k, a time between beats k and k+1 in proportion. Before the first beat and after the last the audio played at
its own speed, so times there shift by a constant. Whisper's words need no second run on the warped file (a second run on a quiet
passage hallucinated on Hello Toni 2, LESSONS row 127). The output must sit under a folder named sandbox.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def mapper(beats: list[float], grid: list[float]):
    def f(t: float) -> float:
        if t <= beats[0]:
            return t + (grid[0] - beats[0])
        if t >= beats[-1]:
            return t + (grid[-1] - beats[-1])
        lo, hi = 0, len(beats) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if beats[mid] <= t:
                lo = mid
            else:
                hi = mid
        a, b = beats[lo], beats[hi]
        return grid[lo] + (t - a) * (grid[hi] - grid[lo]) / (b - a)
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if "sandbox" not in out.resolve().parts:
        print("the output must sit under a folder named sandbox", file=sys.stderr)
        return 2
    m = json.loads(Path(a.map).read_text(encoding="utf-8"))
    f = mapper([float(v) for v in m["beats"]], [float(v) for v in m["grid"]])
    d = json.loads(Path(a.words).read_text(encoding="utf-8"))
    words = d["words"] if isinstance(d, dict) else d
    moved = [{**w, "start": round(f(float(w["start"])), 3), "end": round(f(float(w["end"])), 3)} for w in words]
    res = {**d, "words": moved, "clock": str(a.map)} if isinstance(d, dict) else moved
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("moved %d words onto the clock of %s" % (len(moved), Path(a.map).name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
