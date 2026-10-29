"""Find loops and kicks on this computer that match a song's extracted patterns (skill loops-and-kits; the MCP tool is
find_matching_loops). Read-only on every folder it searches.

    python tools/find_loops.py --like sandbox\\loops\\NAME\\patterns.json --section groove [--in FOLDER ...] [--kick KICK.wav]
        [--kicks-in FOLDER ...] [--top 10] [--out sandbox\\loops\\NAME\\found_groove]

Drum loops are compared by their step profiles (kick, snare or clap, hats; tempo does not matter, the bar does), kicks by pitch, decay and
click brightness. Without --in it searches FL Studio's factory Packs (Loops and Legacy\\Loops; kicks in Drums\\Kicks and the legacy dance
and FPC kicks). Writes OUT.md and OUT.json under a folder named sandbox. Nothing is downloaded and nothing is copied.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import loopsets  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--like", required=True)
    ap.add_argument("--section", required=True)
    ap.add_argument("--in", dest="folders", action="append", default=[])
    ap.add_argument("--kick", default="")
    ap.add_argument("--kicks-in", dest="kick_folders", action="append", default=[])
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    like = Path(a.like)
    rep = json.loads(like.read_text(encoding="utf-8"))
    packs = loopsets.fl_packs()
    folders = [Path(f) for f in a.folders] or ([packs / s for s in loopsets.PACK_LOOPS] if packs else [])
    kfold = [Path(f) for f in a.kick_folders] or ([packs / s for s in loopsets.PACK_KICKS] if packs else [])
    out = Path(a.out) if a.out else like.parent / ("found_%s" % a.section)
    if "sandbox" not in [p.lower() for p in out.resolve().parts]:
        sys.exit("refusing to write %s: output must be under a folder named sandbox" % out)
    try:
        res = loopsets.find(rep, a.section, folders, a.kick or None, kfold, a.top)
    except loopsets.LoopError as e:
        sys.exit(str(e))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    text = loopsets.found_markdown(res, rep["name"], folders)
    out.with_suffix(".md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
