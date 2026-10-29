"""Analyze a bass stem and a vocal stem for the remix: notes, key, a root per bar, vocal phrases and chop candidates.

    python tools/stem_notes.py BASS.wav VOCALS.wav OUT.json --bpm 108.478 --origin 27.3085 [--bars 120]

origin is the time of beat 0 (from drum_hits.json origin_s, which is on the 16th grid). OUT.json has bass {notes, key, roots}, vocals {phrases, chops}.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import bassnotes, dsp, vocalchops


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bass")
    ap.add_argument("vocals")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--origin", type=float, required=True)
    ap.add_argument("--bars", type=int, default=120)
    a = ap.parse_args()
    xb, rb = dsp.load_audio(a.bass)
    t, m, lv = bassnotes.track_pitch(dsp.mono(xb), rb)
    notes = bassnotes.notes_from_track(t, m, lv)
    key = bassnotes.estimate_key(notes)
    roots = bassnotes.roots_per_bar(notes, a.bpm, a.origin - 12 * 240.0 / a.bpm, a.bars)
    xv, rv = dsp.load_audio(a.vocals)
    v = dsp.mono(xv)
    ph = vocalchops.phrases(v, rv)
    ch = vocalchops.chop_candidates(v, rv, ph)
    out = {"bpm": a.bpm, "origin_s": a.origin, "bar0_s": round(a.origin - 12 * 240.0 / a.bpm, 3),
           "bass": {"notes": [{**n, "start": round(n["start"], 3), "end": round(n["end"], 3), "level": round(n["level"], 4)} for n in notes],
                    "key": key, "roots_per_bar": [None if r is None else bassnotes.NAMES[r] for r in roots]},
           "vocals": {"phrases": ph, "chops": ch}}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("bass notes", len(notes), "key", key["tonic"], key["mode"], key["score"], "phrases", len(ph), "chops", len(ch))
    print("roots", out["bass"]["roots_per_bar"][:40])
    print("phrases", [(p["start"], p["end"]) for p in ph[:25]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
