"""Per-section loudness and balance report for a render of the tech-house remix.

    python tools/render_report.py RENDER.wav [--bpm 124]

Prints, for each arrangement section, the peak, integrated LUFS (when long enough), short-term maximum and the share of energy in sub (20-60 Hz), bass (60-250),
mids (250-4k) and highs (4k+), plus the whole-file integrated loudness, true-peak estimate and the count of clipped samples.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pyloudnorm as pyln  # noqa: E402
import soundfile as sf  # noqa: E402

from coproducer import remixplan  # noqa: E402


def bands(x: np.ndarray, rate: int) -> list[float]:
    m = x.mean(axis=1)
    sp = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
    fr = np.fft.rfftfreq(len(m), 1 / rate)
    edges = [(20, 60), (60, 250), (250, 4000), (4000, 20000)]
    e = [float(sp[(fr >= a) & (fr < b)].sum()) for a, b in edges]
    t = sum(e) + 1e-30
    return [v / t for v in e]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--bpm", type=float, default=remixplan.BPM)
    a = ap.parse_args()
    x, rate = sf.read(a.wav, dtype="float64", always_2d=True)
    meter = pyln.Meter(rate)
    bar = 240.0 / a.bpm
    print("file %.1fs, %d Hz, %d ch" % (len(x) / rate, rate, x.shape[1]))
    print("%-7s %-10s %7s %8s %8s   sub  bass   mid  high" % ("bars", "section", "peak", "LUFS", "stMax"))
    for s in remixplan.SECTIONS:
        seg = x[int(s["start"] * bar * rate) : int(s["end"] * bar * rate)]
        if len(seg) < rate:
            continue
        pk = 20 * np.log10(np.abs(seg).max() + 1e-12)
        try:
            lu = meter.integrated_loudness(seg)
        except ValueError:
            lu = float("nan")
        st = max((meter.integrated_loudness(seg[i : i + 3 * rate]) for i in range(0, len(seg) - 3 * rate, rate)), default=float("nan"))
        b = bands(seg, rate)
        print("%3d-%-3d %-10s %6.1f %8.1f %8.1f   %.2f  %.2f  %.2f  %.2f" % (s["start"], s["end"], s["name"], pk, lu, st, *b))
    clipped = int((np.abs(x) >= 0.999).sum())
    print("whole file: peak %.2f dBFS, integrated %.1f LUFS, clipped samples %d" % (20 * np.log10(np.abs(x).max() + 1e-12), meter.integrated_loudness(x), clipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
