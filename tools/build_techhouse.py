"""Build the remix project from a song plan: editable drums, bass, stabs and vocal chops as patterns, the stretched vocal and an FX bed as playlist audio.

    python tools/build_techhouse.py BASE.flp DTP.flp AUDIODIR OUT.flp [--plan plans/NAME.json] [--origin SECONDS]

BASE.flp is the stem project (its stem channels and clips are replaced), DTP.flp supplies the Sytrus patches (Remix Sub for the sub bass, Trance pluck for stabs and
the arp), AUDIODIR holds the files from tools/techhouse_audio.py. OUT must sit under a folder named sandbox; the inputs are never written. Without --plan the
first song's values built into remixplan are used.

--serum TEMPLATE.flp clones the sub, stab and arp channels from a project whose Serum 2 channels have the sounds loaded, found by preset name (docs/SERUM_MCP.md);
--serum-preset KEY=NAME picks other preset names, --serum-db KEY=DB sets their mixer level, --kit KEY=WAV replaces a kit voice, --solo keeps only some mixer groups.
The logic lives in src/coproducer/remixbuild.py (also the module build_remix_project).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import remixbuild, songplan  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("base", "dtp", "audio", "out"):
        ap.add_argument(name)
    ap.add_argument("--plan", default="", help="song plan JSON (plans/NAME.json)")
    ap.add_argument("--serum", default="")
    ap.add_argument("--serum-preset", action="append", default=[], metavar="KEY=NAME")
    ap.add_argument("--serum-db", action="append", default=[], metavar="KEY=DB")
    ap.add_argument("--kit", action="append", default=[], metavar="KEY=WAV")
    ap.add_argument("--stab-offbeat", action="store_true")
    ap.add_argument("--solo", default="", help="comma list of mixer groups to keep audible: kick,clap,hats,perc,reese,sub,stab,arp,chops,vocal,fx")
    ap.add_argument("--origin", type=float, default=None, help="seconds into the original stem where its bar grid is anchored (default: the plan's)")
    a = ap.parse_args()
    try:
        if a.plan:
            songplan.apply(songplan.load(a.plan))
        rep = remixbuild.build(a.base, a.dtp, a.audio, a.out, origin=a.origin, serum=a.serum, serum_preset=a.serum_preset, serum_db=a.serum_db, kit=a.kit,
                               stab_offbeat=a.stab_offbeat, solo=a.solo)
    except (remixbuild.BuildError, songplan.PlanError) as e:
        sys.exit(str(e))
    print("vocal overlaps:", len(rep["overlap_notes"]))
    for line in rep["overlap_notes"]:
        print("  note:", line)
    print("wrote", rep["out"])
    print("tempo", rep["tempo"], "channels", rep["channels"], "patterns", rep["patterns"], "playlist items", rep["playlist_items"])
    print("pattern counts", rep["pattern_counts"])
    print("vocal clips (pos_ticks, len_ticks, start_ms, end_ms)", rep["vocal_clips"])
    print("channel ids", rep["channel_ids"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
