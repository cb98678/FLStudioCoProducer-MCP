"""Compare a note rendered from a synth patch with a target sound and say what to change. Run from the repo root.

    python tools/synth_match.py TARGET.wav CANDIDATE.wav [--fmin 20 --fmax 500]

Render one held note from the patch (a short project with only that channel, or a solo render), then run this. Repeat until the match line is true.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import synthmatch  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("candidate")
    ap.add_argument("--fmin", type=float, default=20)
    ap.add_argument("--fmax", type=float, default=500)
    a = ap.parse_args()
    t, sr = sf.read(a.target)
    c, sr2 = sf.read(a.candidate)
    T = synthmatch.describe_tone(t, sr, a.fmin, a.fmax)
    C = synthmatch.describe_tone(c, sr2, a.fmin, a.fmax)
    print(json.dumps({"target": T, "candidate": C, **synthmatch.compare_tones(T, C)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
