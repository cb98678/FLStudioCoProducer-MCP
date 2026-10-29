"""Splice one vocal stem from several time-aligned takes of it (the same file processed different ways, such as three Newtone settings),
choosing a take per time region with short crossfades, after trimming a lead-in that was added for an editor's grid.

    python tools/splice_takes.py --take robotic=A.wav --take middle=B.wav --take smooth=C.wav --default smooth \
        --region 105.0:122.4=robotic --region 19.6:37.3=middle --trim-start 0.7323 --out sandbox\\...\\vocals_tuned.wav

Regions are seconds of the trimmed file (the original stem's own clock). Every output stays under a folder named sandbox.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def splice(takes: dict, default: str, regions: list[tuple[float, float, str]], trim_s: float = 0.0, xfade_s: float = 0.03) -> tuple[np.ndarray, int]:
    data, rate = {}, None
    for name, path in takes.items():
        x, r = sf.read(path, dtype="float32", always_2d=True)
        if rate is not None and r != rate:
            sys.exit("take %s is at %d Hz, not %d" % (name, r, rate))
        rate = r
        data[name] = x[int(round(trim_s * r)):]
    n = min(len(x) for x in data.values())
    out = data[default][:n].copy()
    k = max(1, int(xfade_s * rate))
    for t0, t1, name in sorted(regions):
        a, b = max(0, int(t0 * rate)), min(n, int(t1 * rate))
        if b - a < 2 * k:
            continue
        env = np.ones(b - a, dtype="float32")
        env[:k] = np.linspace(0, 1, k)
        env[-k:] = np.linspace(1, 0, k)
        out[a:b] = out[a:b] * (1 - env[:, None]) + data[name][a:b] * env[:, None]
    return out, rate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", action="append", required=True, help="NAME=PATH (repeatable)")
    ap.add_argument("--default", required=True)
    ap.add_argument("--region", action="append", default=[], help="T0:T1=NAME in seconds of the trimmed file (repeatable)")
    ap.add_argument("--trim-start", type=float, default=0.0)
    ap.add_argument("--xfade-ms", type=float, default=30.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if "sandbox" not in [p.lower() for p in out.resolve().parts]:
        sys.exit("refusing to write %s: output must be under a folder named sandbox" % out)
    takes = dict(t.split("=", 1) for t in a.take)
    regions = []
    for r in a.region:
        span, name = r.rsplit("=", 1)
        t0, t1 = (float(v) for v in span.split(":"))
        regions.append((t0, t1, name))
    if a.default not in takes or any(n not in takes for *_x, n in regions):
        sys.exit("every region and the default must name a --take")
    y, rate = splice(takes, a.default, regions, a.trim_start, a.xfade_ms / 1000.0)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), y, rate, subtype="PCM_24")
    print(json.dumps({"out": str(out), "seconds": round(len(y) / rate, 3), "regions": len(regions), "takes": sorted(takes)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
