"""Prepare a vocal stem for the chunking, Newtime, Newtone and the build: lift the passages sung far under the rest, then normalize.

    python tools/level_vocal.py --in VOCALS.wav --out VOCALS_lev.wav [--under-db 12] [--to-db 6] [--peak-db -1] [--gap-s 0.3]

A phone or room recording sings a verse and whispers a bridge; a separated stem of it peaks at -25 dBFS. Both defeat the measurements
that come after (Newtime's drawn waveform matched nothing at -25 dBFS; a whispered passage 20 dB under the singing sat below the
chunker's floor and Whisper's ear, Hello Toni 2, LESSONS rows 127 and 129). This finds the phrases (voice above an adaptive floor,
joined across gaps under --gap-s, the chunker's phrase gap), measures each one's RMS, and lifts every run of phrases more than
--under-db under the median phrase up to --to-db under it with 60 ms ramps (a soft word inside a sung line is not touched: the lift
applies to whole phrases, and only to the ones far under), then scales the whole file to --peak-db. Writes OUT and OUT.levels.json (every passage, its level
before and after, the gain applied). The output must sit under a folder named sandbox; the input is only read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def passages(mono: np.ndarray, rate: int, gap_s: float, win_s: float = 0.01) -> tuple[list[tuple[float, float]], float]:
    n = max(1, int(win_s * rate))
    m = len(mono) // n
    env = 20 * np.log10(np.sqrt(np.mean(mono[: m * n].reshape(m, n) ** 2, axis=1) + 1e-14))
    loud = np.percentile(env[env > -90], 95) if np.any(env > -90) else -20.0
    floor = loud - 30.0
    on = env > floor
    runs, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append([start * win_s, i * win_s])
            start = None
    if start is not None:
        runs.append([start * win_s, m * win_s])
    out: list[list[float]] = []
    for r in runs:
        if out and r[0] - out[-1][1] < gap_s:
            out[-1][1] = r[1]
        else:
            out.append(list(r))
    return [(a, b) for a, b in out if b - a >= 0.3], float(floor)


def rms_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--under-db", type=float, default=12.0, help="a passage this far under the median passage gets lifted")
    ap.add_argument("--to-db", type=float, default=6.0, help="lifted to this far under the median (not all the way: it stays a quiet passage)")
    ap.add_argument("--peak-db", type=float, default=-1.0)
    ap.add_argument("--gap-s", type=float, default=0.3)
    a = ap.parse_args()
    out = Path(a.out)
    if "sandbox" not in out.resolve().parts:
        print("the output must sit under a folder named sandbox", file=sys.stderr)
        return 2
    import soundfile as sf

    x, rate = sf.read(a.src, dtype="float64", always_2d=True)
    mono = x.mean(axis=1)
    ps, floor = passages(mono, rate, a.gap_s)
    levels = [rms_db(mono[int(s * rate):int(e * rate)]) for s, e in ps]
    med = float(np.median(levels)) if levels else 0.0
    g = np.ones(len(x))
    ramp = int(0.06 * rate)
    rows = []
    for (s, e), lv in zip(ps, levels):
        gain_db = 0.0
        if lv < med - a.under_db:
            gain_db = (med - a.to_db) - lv
            i0, i1 = int(s * rate), int(e * rate)
            lin = 10 ** (gain_db / 20)
            g[i0:i1] = lin
            g[max(0, i0 - ramp):i0] = np.linspace(1.0, lin, min(ramp, i0))
            g[i1:min(len(g), i1 + ramp)] = np.linspace(lin, 1.0, min(ramp, len(g) - i1))
        rows.append({"start_s": round(s, 2), "end_s": round(e, 2), "rms_db": round(lv, 1), "gain_db": round(gain_db, 1)})
    y = x * g[:, None]
    peak = float(np.abs(y).max()) or 1.0
    norm = 10 ** (a.peak_db / 20) / peak
    y *= norm
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), y, rate, subtype="PCM_24")
    rep = {"source": a.src, "floor_db": round(floor, 1), "median_passage_db": round(med, 1), "normalize_db": round(20 * np.log10(norm), 1),
           "lifted": sum(1 for r in rows if r["gain_db"]), "passages": rows}
    out.with_name(out.stem + ".levels.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k != "passages"}))
    for r in rows:
        if r["gain_db"]:
            print("lifted %.1f-%.1f s by %+.1f dB" % (r["start_s"], r["end_s"], r["gain_db"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
