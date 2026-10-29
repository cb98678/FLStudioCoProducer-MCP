"""List pattern notes of a project as absolute times, and optionally compare them with detected drum hits.

    python tools/flp_note_times.py PROJECT.flp [--hits drum_hits.json]

Reads the playlist pattern clips and the tempo, so it checks what the file will play without opening FL Studio. With --hits it prints, per drum,
how far each note is from the nearest detected hit (milliseconds) and how many detected hits have no note within 80 ms.
"""
import argparse
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import flpfile as F

KIND_BY_NAME = {"808 Kick": "kick", "808 Snare": "snare", "808 HiHat": "hat"}


def note_times(f: F.Flp) -> dict[int, list[float]]:
    """{channel: [seconds]} for every pattern note placed by the playlist."""
    pats: dict[int, bytes] = {}
    cur = None
    for e, v in f.events[: f._playlist_index()]:
        if e == F.EV_NEWPAT:
            cur = struct.unpack("<H", v)[0]
        elif e == F.EV_PATNOTES and cur is not None:
            pats[cur] = pats.get(cur, b"") + v
    sec_per_tick = 60.0 / f.tempo() / F.TICKS_PER_BEAT
    out: dict[int, list[float]] = {}
    for it in f.playlist_items():
        item = struct.unpack("<H", it[6:8])[0]
        if item <= F.PATTERN_BASE:
            continue
        start = struct.unpack("<I", it[0:4])[0]
        data = pats.get(item - F.PATTERN_BASE, b"")
        for k in range(0, len(data) - F.NOTE_SIZE + 1, F.NOTE_SIZE):
            pos, _, ch = struct.unpack("<IHH", data[k : k + 8])
            out.setdefault(ch, []).append((start + pos) * sec_per_tick)
    return {c: sorted(v) for c, v in out.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("flp")
    ap.add_argument("--hits")
    a = ap.parse_args()
    f = F.Flp.load(a.flp)
    times = note_times(f)
    print("tempo", f.tempo(), {c: len(v) for c, v in times.items()})
    if a.hits:
        with open(a.hits, encoding="utf-8") as fh:
            hits = json.load(fh)["hits"]
        for ch, ts in times.items():
            name = f.get_text(ch, F.EV_CH_NAME)
            kind = KIND_BY_NAME.get(name)
            h = np.array([t for t, k, _ in hits if k == kind])
            if not len(h) or not ts:
                continue
            tn = np.array(ts)
            err = np.array([(tn[np.argmin(np.abs(tn - x))] - x) for x in h]) * 1000
            near = np.abs(err) <= 80
            print(name, "hits", len(h), "notes", len(tn), "hits with a note within 80 ms", int(near.sum()),
                  "mean error ms %.2f" % err[near].mean(), "mean abs ms %.2f" % np.abs(err[near]).mean(), "max abs ms %.1f" % np.abs(err[near]).max())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
