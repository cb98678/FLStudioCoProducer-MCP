"""Cut clean loops, a drum kit and patterns from a song's stems (skill loops-and-kits; the MCP tool is extract_song_loops).

    python tools/extract_loops.py --song sandbox\\songs\\NAME --sections "groove:13-20,drop:29-36,break:21-27" [--out sandbox\\loops\\NAME]
        [--loop-bars 1,2,4] [--kit-from groove] [--hook 1-2] [--name NAME]

--song is a build_song_analysis folder (song_analysis.json and its stems). Sections are bar ranges, 1-based and inclusive, numbered like
the analysis grid (bar 1 is the grid's first bar). For each section: the drum, bass, music (the 'other' stem) and full-instrumental loops,
every repetition aligned and averaged so the bleed cancels; the drum pattern in three bands; the bass notes. The kit (kick, snare or clap,
hat) comes from the --kit-from section (default: the section with the most bars). --hook writes those vocal bars as a cut (no averaging:
a hook is sung once). Writes WAV and MIDI files, patterns.json and README.md under OUT, which must sit under a folder named sandbox. The
stems are only read.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import loopsets  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--song", required=True)
    ap.add_argument("--sections", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--loop-bars", default="1,2,4")
    ap.add_argument("--kit-from", default="")
    ap.add_argument("--hook", default="")
    a = ap.parse_args()
    name = a.name or Path(a.song).name
    out = Path(a.out) if a.out else HOME / "sandbox" / "loops" / name
    if "sandbox" not in [p.lower() for p in out.resolve().parts]:
        sys.exit("refusing to write %s: output must be under a folder named sandbox" % out)
    try:
        rep = loopsets.extract(a.song, a.sections, out, name=a.name, loop_bars=[int(v) for v in a.loop_bars.split(",") if v.strip()],
                               kit_from=a.kit_from, hook=a.hook)
    except loopsets.LoopError as e:
        sys.exit(str(e))
    print(loopsets.readme(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
