"""Render an FX bed WAV from a cue plan (JSON). Run from the repo root.

    python tools/fx_bed.py cues.json OUT.wav --bpm 140 --beats 321.302

cues.json is {"master_db": 0.0, "cues": [{"kind": "impact", "bar": 8, "gain_db": 0}, ...]}; kinds and fields are in coproducer/fxbed.py.
No ducking or level moves are baked in: use automation clips for those (coproducer.automation).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

from coproducer import fxbed  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, default=140.0)
    ap.add_argument("--beats", type=float, required=True, help="length of the bed in beats")
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    x = fxbed.render_bed(plan["cues"], a.bpm, a.beats) * 10 ** (plan.get("master_db", 0.0) / 20)
    peak = float(np.max(np.abs(x)))
    if peak > 0.98:
        print("peak %.3f would clip; lower master_db by %.1f dB" % (peak, 20 * np.log10(peak / 0.98)))
        return 2
    sf.write(a.out, x.astype(np.float32), fxbed.SR, subtype="PCM_16")
    print("wrote %s: %d samples, peak %.1f dBFS" % (a.out, len(x), 20 * np.log10(peak + 1e-12)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
