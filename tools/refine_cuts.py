"""Place every vocal cut of the tech-house remix on whole words, with Whisper as the judge (src/coproducer/cutrefine.py), and write cuts.json.

    python tools/refine_cuts.py VOCALS.wav OUT_cuts.json [--model openai/whisper-large-v3]

Run with the pinned critique environment (models\\envs\\critique\\Scripts\\python.exe, see docs/DEPENDENCIES.md), which has torch, transformers and the cached Whisper snapshot. It reads remixplan.CHOPS and remixplan.VOCAL_CLIPS. For each cut it records the
start and end in original-stem seconds, whether the recogniser confirmed each edge, and the transcripts it saw, so a doubtful cut can be inspected.
tools/techhouse_audio.py uses the file when given --cuts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import soundfile as sf  # noqa: E402

from asr_probe import load, transcribe  # noqa: E402
from coproducer import cutrefine, remixplan, vocalchops  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vocals")
    ap.add_argument("out")
    ap.add_argument("--model", default="openai/whisper-large-v3")
    a = ap.parse_args()
    x, rate = sf.read(a.vocals, dtype="float32", always_2d=True)
    mono = x.mean(axis=1)
    gp = vocalchops.gaps(mono, rate)
    asr = load(a.model)
    cache: dict[tuple[int, int], str] = {}

    def rec(seg, sr):
        k = (len(seg), int(float(abs(seg).sum()) * 1000))
        if k not in cache:
            cache[k] = transcribe(asr, seg, sr)
        return cache[k]

    result = {"chops": {}, "clips": []}

    def show(tag, r):
        for side in ("start", "end"):
            print("    %s %s: %s" % (tag, side, " | ".join("%.2f [%s] [%s]" % (c, lt, rt) for c, lt, rt in r["evidence"][side])), flush=True)

    for name, spec in remixplan.CHOPS.items():
        r = cutrefine.refine(mono, rate, gp, spec, rec)
        result["chops"][name] = r
        show(name, r)
        print("%-10s hint %.2f-%.2f -> %.3f-%.3f  start seam %s, end seam %s  (%s)" % (name, *r["hint"], r["start"], r["end"], r["start_kind"], r["end_kind"], spec["words"]), flush=True)
    for (bar, ob, h0, h1, label, mode), w in zip(remixplan.VOCAL_CLIPS, remixplan.CLIP_WORDS):
        spec = {"start": h0, "end": h1, "end_mode": mode, **w}
        r = cutrefine.refine(mono, rate, gp, spec, rec, reach=0.6)
        r["label"] = label
        r["end"] = round(r["end"] + 0.25, 3)  # a long clip rings out: the hand-fixed "okay" clip (v3e_userfix) ended 0.25 s after the gap where the voice stops
        result["clips"].append(r)
        print("%-26s hint %.2f-%.2f -> %.3f-%.3f  start seam %s, end seam %s" % (label, *r["hint"], r["start"], r["end"], r["start_kind"], r["end_kind"]), flush=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
