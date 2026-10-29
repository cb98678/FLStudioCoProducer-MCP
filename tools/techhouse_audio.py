"""Make the audio for a remix build (the work is in coproducer.remixaudio): the vocal stem stretched to the remix tempo, vocal chop one-shots,
the style's drum kit and bass sample, and the FX bed.

    python tools/techhouse_audio.py OUTDIR --vocals VOCALS.wav [--plan plans/NAME.json] [--cuts CUTS.json] [--pitch RATIO]

Needs ffmpeg with the rubberband filter on PATH. Writes into OUTDIR (under a folder named sandbox):
    vocals_<bpm>.wav      the vocal stem, tempo x bpm * vocal multiple / source bpm, 16-bit stereo
    CP_Chop_<name>.wav    one-shot per entry of remixplan.CHOPS (start on a syllable onset, end per its end_mode), plus CP_Chop_<name>_echo.wav for remixplan.ECHOED
    CP_Kick.wav ...       the nine-voice kit from oneshots.write_kit (a style may replace voices)
    CP_Reese.wav          the style's bass sample (reese, growl, 808), tuned to A1 at sampler key 60
    FX_bed.wav            impacts, sweeps, risers and downlifters at the cue positions
    techhouse_audio.json  stretch ratio, measured delay of the stretched file, chop spans, levels
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import remixaudio, songplan  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--vocals", required=True)
    ap.add_argument("--cuts", default="", help="cuts.json from tools/refine_cuts.py (recogniser-checked cut points); without it the cuts are placed by signal alone")
    ap.add_argument("--pitch", type=float, default=None, help="rubberband pitch ratio (tuning correction); default: the plan's")
    ap.add_argument("--plan", default="", help="a plans/NAME.json; default: the plan remixplan ships with (the first song)")
    a = ap.parse_args()
    if a.plan:
        songplan.apply(songplan.load(a.plan))
    try:
        remixaudio.prepare(a.outdir, a.vocals, a.cuts, a.pitch)
    except remixaudio.AudioError as e:
        sys.exit(str(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
