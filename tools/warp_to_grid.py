"""Fit a freely played recording to a steady beat grid without changing its pitch (a tempo map): every beat of the recording lands on
the beat of a fixed tempo, so a stem recorded without a click (an acoustic guitar and voice drifting between 83 and 90 bpm) sits on a
remix grid. One rubberband pass with the tempo changed at every beat (ffmpeg's asendcmd into its rubberband filter, formants preserved),
so there are no cuts or crossfades inside notes; measured 2 to 7 ms off on a click track.

    python tools/warp_to_grid.py --beats BEATS.json --bpm 86 --in IN.wav --out OUT.wav [--in IN2.wav --out OUT2.wav ...] [--check]

BEATS.json: the recording's beat times in seconds, ascending (from its strums or a beat tracker, checked by hand). The first beat keeps
its own time; beat k lands at first + k * 60 / bpm; before the first and after the last beat the audio plays at its own speed. --check
warps a click track built from the beats and reports how far each click lands from its grid beat. Outputs must sit under a folder named
sandbox; inputs are only read. Writes OUT.map.json beside each output (the beats, the grid and the tempo map).
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def tempo_map(beats: list[float], bpm: float) -> list[tuple[float, float]]:
    """(source time, rubberband tempo) from each beat on: the beat's own length over the grid's. Before the first beat the tempo is 1."""
    target = 60.0 / bpm
    out = [(0.0, 1.0)]
    for a, b in zip(beats, beats[1:]):
        if b - a <= 0.05:
            raise ValueError("beats %.3f and %.3f are too close" % (a, b))
        out.append((a, (b - a) / target))
    out.append((beats[-1], 1.0))
    return out


def grid(beats: list[float], bpm: float) -> list[float]:
    return [beats[0] + k * 60.0 / bpm for k in range(len(beats))]


def commands(tm: list[tuple[float, float]]) -> str:
    return "; ".join("%.4f rubberband tempo %.6f" % (t, r) for t, r in tm)


def warp(src: Path, dst: Path, tm: list[tuple[float, float]], quality: str = "quality") -> None:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg not found on PATH")
    af = "asendcmd=c='%s',rubberband=tempo=%.6f:pitch=1:formant=preserved:transients=mixed:pitchq=%s" % (commands(tm), tm[0][1], quality)
    p = subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af", af, "-c:a", "pcm_s24le", str(dst)], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError("ffmpeg failed: " + p.stderr[-800:])


def expected(t: float, tm: list[tuple[float, float]]) -> float:
    """Output time of source time t under the tempo map."""
    out = 0.0
    for (a, r), (b, _r2) in zip(tm, tm[1:] + [(float("inf"), 1.0)]):
        if t <= a:
            break
        out += (min(t, b) - a) / r
    return out


def check(beats: list[float], bpm: float, tm: list[tuple[float, float]], rate: int = 44100) -> dict:
    """Warp a click track made from the beats and measure where each click lands against the grid."""
    import numpy as np
    import soundfile as sf
    n = int((beats[-1] + 1.0) * rate)
    y = np.zeros(n)
    for b in beats:
        i = int(b * rate)
        y[i:i + 200] += np.hanning(200) * 0.8
    t = np.arange(n) / rate
    y += 0.05 * np.sin(2 * np.pi * 220 * t)
    with tempfile.TemporaryDirectory() as d:
        a, z = Path(d) / "clicks.wav", Path(d) / "warped.wav"
        sf.write(str(a), y, rate)
        warp(a, z, tm)
        w, _ = sf.read(str(z), always_2d=True)
    env = np.abs(w.mean(axis=1))
    got, i = [], 0
    while i < len(env):
        if env[i] > 0.3:
            got.append(i / rate)
            i += int(0.3 * rate)
        else:
            i += 1
    g = grid(beats, bpm)
    errs = [1000 * (x - e) for x, e in zip(got, g)]
    return {"clicks": len(beats), "found": len(got), "max_abs_ms": round(max(abs(e) for e in errs), 1) if errs else None,
            "mean_ms": round(sum(errs) / len(errs), 1) if errs else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True)
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--in", dest="ins", action="append", default=[])
    ap.add_argument("--out", dest="outs", action="append", default=[])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if len(a.ins) != len(a.outs):
        sys.exit("give one --out per --in")
    beats = [float(x) for x in json.loads(Path(a.beats).read_text(encoding="utf-8"))]
    tm = tempo_map(beats, a.bpm)
    g = grid(beats, a.bpm)
    report = {"bpm": a.bpm, "beats": beats, "grid": g, "tempo_map": tm, "origin_s": beats[0],
              "ratio_min": round(min(r for _t, r in tm[1:-1]), 4), "ratio_max": round(max(r for _t, r in tm[1:-1]), 4)}
    if a.check:
        report["check"] = check(beats, a.bpm, tm)
        print("check:", report["check"])
    for src, dst in zip(a.ins, a.outs):
        dst = Path(dst)
        if "sandbox" not in [p.lower() for p in dst.resolve().parts]:
            sys.exit("refusing to write %s: output must be under a folder named sandbox" % dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        warp(Path(src), dst, tm)
        dst.with_suffix(".map.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
        print("warped", src, "->", dst)
    print("tempo ratios %.3f to %.3f, %d beats, origin %.3f s" % (report["ratio_min"], report["ratio_max"], len(beats), beats[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
