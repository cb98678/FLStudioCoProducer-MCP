"""Transcribe the finished chops, and the chops joined the way the pattern plays them, to catch a leftover or missing syllable.

    python tools/chop_qa.py AUDIODIR            (run with the interpreter that has torch and transformers)

Prints one line per CP_Chop_<name>.wav (dry) and for each pair in PAIRS joined with 80 ms of silence. A chop that reads as the wrong word, or a join that reads
as a stutter ("whis key drowns"), is a bad cut. Whisper is noisy on very short clips, so read these as evidence, not as a verdict.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

from asr_probe import load, transcribe  # noqa: E402

PAIRS = [("whiskey", "drowns"), ("pickup", "friends"), ("friends", "lowplaces"), ("blues", "bluesaway"), ("pickup", "hook")]


def main() -> int:
    d = sys.argv[1]
    asr = load("openai/whisper-large-v3")
    names = sorted(f[8:-4] for f in os.listdir(d) if f.startswith("CP_Chop_") and f.endswith(".wav") and not f.endswith("_echo.wav"))
    clips = {n: sf.read(os.path.join(d, "CP_Chop_%s.wav" % n), dtype="float32", always_2d=True) for n in names}
    for n in names:
        x, sr = clips[n]
        print("%-22s %s" % (n, transcribe(asr, x, sr)), flush=True)
    for a, b in PAIRS:
        if a in clips and b in clips:
            x, sr = clips[a]
            y, _ = clips[b]
            j = np.concatenate([x, np.zeros((int(0.08 * sr), x.shape[1]), dtype="float32"), y])
            print("%-22s %s" % (a + " + " + b, transcribe(asr, j, sr)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
