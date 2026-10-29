"""Compare a render with a reference remix bar by bar: third-octave level difference, normalized to the 250 Hz to 4 kHz band.

    python tools/spec_match.py RENDER.wav REF.wav BAR_MAP.json [--bpm 140] [--shift-steps 2] [--last-bar 58]

BAR_MAP.json maps reference bar to render bar ({"0": 0, "1": 1, ...}). Bars past --last-bar and bars that fall outside either file are skipped,
because silent tail bars drag every band down. Positive means the render is louder than the reference at that frequency.
Reference MP3s are low-passed near 16 kHz, so ignore the top bands when the reference is lossy.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import scipy.signal as ss
import soundfile as sf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("ref")
    ap.add_argument("bar_map")
    ap.add_argument("--bpm", type=float, default=140)
    ap.add_argument("--shift-steps", type=float, default=2)
    ap.add_argument("--last-bar", type=int, default=10**6)
    a = ap.parse_args()
    cur, sr = sf.read(a.render)
    ref, sr2 = sf.read(a.ref)
    if sr2 != sr:
        g = np.gcd(sr, sr2)
        ref = ss.resample_poly(ref, sr // g, sr2 // g, axis=0)
    cur, ref = (x.mean(1) if x.ndim > 1 else x for x in (cur, ref))
    bar = int(round(4 * 60 / a.bpm * sr))
    shift = int(round(a.shift_steps * 60 / a.bpm / 4 * sr))
    bands = [25 * 2 ** (i / 3) for i in range(0, 31)]
    f = np.fft.rfftfreq(bar, 1 / sr)
    w = np.hanning(bar)

    def third(x: np.ndarray) -> np.ndarray:
        p = np.abs(np.fft.rfft(x * w)) ** 2
        return np.array([10 * np.log10(p[(f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].sum() + 1e-12) for c in bands])

    R, C = [], []
    for r, o in sorted((int(k), v) for k, v in json.load(open(a.bar_map)).items()):
        s = r * bar + shift
        if r >= a.last_bar or s + bar > len(ref) or o * bar + bar > len(cur):
            continue
        R.append(third(ref[s : s + bar]))
        C.append(third(cur[o * bar : o * bar + bar]))
    d = np.mean(C, 0) - np.mean(R, 0)
    base = float(np.mean(d[(np.array(bands) >= 250) & (np.array(bands) <= 4000)]))
    print("bars used %d, 250 Hz to 4 kHz offset %.1f dB (render minus reference)" % (len(R), base))
    for c, x in zip(bands, d - base):
        print("%6.0f Hz %+5.1f" % (c, x))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
