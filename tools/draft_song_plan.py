"""Draft a song plan for a new song from its analysis files.

    python tools/draft_song_plan.py WORDS.json HITS.json OUT.json --name NAME [--title "Song Title"] [--bass STEM_NOTES.json] [--key-pc N] [--bpm 124]

WORDS.json is the vocal stem's Whisper word times ({text, words: [{word, start, end}]}, from tools/transcribe_vocals.py), HITS.json is the drum stem's hits
(tools/drum_hits.py), STEM_NOTES.json holds the bass stem's key and roots per bar (tools/stem_notes.py). Give --bass or --key-pc. The result is a draft: read the
chops and roles, listen, then build with tools/build_techhouse.py --plan OUT.json. The logic lives in src/coproducer/songanalysis.py (module build_song_plan).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import songanalysis, songplan  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for n in ("words", "hits", "out"):
        ap.add_argument(n)
    ap.add_argument("--name", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--bass", default="")
    ap.add_argument("--key-pc", type=int, default=None)
    ap.add_argument("--bpm", type=float, default=124.0)
    a = ap.parse_args()
    words, hits = json.load(open(a.words, encoding="utf-8")), json.load(open(a.hits, encoding="utf-8"))
    bass = json.load(open(a.bass, encoding="utf-8"))["bass"] if a.bass else {}
    key_pc = a.key_pc if a.key_pc is not None else bass.get("key", {}).get("tonic_pc")
    if key_pc is None:
        sys.exit("give --bass or --key-pc")
    down = songanalysis.find_downbeat(songanalysis.hit_rows(hits["hits"]), hits["bpm"], hits["offset_s"])
    try:
        plan = songanalysis.draft_plan(a.name, songanalysis.tokens(words["words"]), source_bpm=hits["bpm"], key_pc=key_pc, origin_s=down["origin_s"],
                                       roots=bass.get("roots_per_bar"), title=a.title, bpm=a.bpm)
    except ValueError as e:
        sys.exit(str(e))
    problems = songplan.validate(plan)
    songplan.save(plan, a.out)
    print("downbeat %.4f s (confidence %.2f)" % (down["origin_s"], down["confidence"]))
    print("hook:", plan["chops"]["hook"])
    print("chops:", ", ".join(sorted(plan["chops"])))
    print("roles:", json.dumps(plan["roles"]))
    print("problems:", problems or "none")
    for n in plan["notes"]:
        print("note:", n)
    print("wrote", a.out)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
