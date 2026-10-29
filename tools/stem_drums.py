"""Rebuild a drum stem as editable channel-rack drums in a sandbox copy of a project.

    python tools/stem_drums.py IN.flp OUT.flp drum_hits.json --kick CH --snare CH [--hat CH] [--mute-ch CH] [--set-tempo] [--track 44]

Reads the notes from tools/drum_hits.py, puts kick, snare and hat on the given sampler channels as one pattern per distinct bar with a one-bar
playlist clip each, keeps the audio's offset so the notes line up with the stem, optionally mutes the stem's channel and sets the project tempo.
The input is never written; OUT must sit under a folder named sandbox.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import flpfile

KEY = 60  # C5 plays a channel-rack sampler at the sample's own pitch


def bucket(vel: int) -> int:
    """Three velocity levels (soft, normal, accent) so repeated bars share one pattern and the part stays easy to edit."""
    return 72 if vel < 70 else 98 if vel < 105 else 118


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("flp")
    ap.add_argument("out")
    ap.add_argument("hits")
    ap.add_argument("--kick", type=int)
    ap.add_argument("--snare", type=int)
    ap.add_argument("--hat", type=int)
    ap.add_argument("--mute-ch", type=int)
    ap.add_argument("--set-tempo", action="store_true")
    ap.add_argument("--track", type=int, default=44)
    ap.add_argument("--base-id", type=int, default=0)
    a = ap.parse_args()
    if "sandbox" not in [p.lower() for p in os.path.abspath(a.out).split(os.sep)]:
        sys.exit("refusing to write %s: output must be under a folder named sandbox" % a.out)
    with open(a.hits, encoding="utf-8") as fh:
        spec = json.load(fh)
    chans = {"kick": a.kick, "snare": a.snare, "hat": a.hat}
    shift = spec["origin_s"] * spec["bpm"] / 60.0  # beat 0 of the rows is this many beats into the audio, so the notes land on the recorded hits
    rows = [(start + shift, dur, KEY, bucket(vel), chans[kind]) for kind, items in spec["notes"].items() if chans.get(kind) is not None
            for start, dur, _key, vel in items]
    f = flpfile.Flp.load(a.flp)
    if a.set_tempo:
        f.set_tempo(spec["bpm"])
    if a.mute_ch is not None:
        f.set_enabled(a.mute_ch, False)
    m = f.add_part("DRUMS", flpfile.notes_by_bar_channels(rows), a.track, a.base_id or f.next_pattern_id(1))
    f.save(a.out)
    print("wrote", a.out, "notes", len(rows), "bars", len(m), "patterns", len(set(m.values())), "tempo", f.tempo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
