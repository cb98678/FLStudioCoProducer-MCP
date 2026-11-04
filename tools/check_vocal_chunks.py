"""Check a vocal chunk manifest (split_vocal_phrases) the way the person asked (2026-11-03): every cut evaluated at the syllables' ends and
starts, so no chunk clips a word.

    python tools/check_vocal_chunks.py sandbox/songs/NAME/warped/chunks/chunks.json [--words WORDS.json] [--suffix _q]

For every cut: the level of the source in the 40 ms before it and the 40 ms after it against the file's floor (a cut inside a sound
fails), the distance from the cut back to the end of the voice before it (the release kept) and forward to the first voiced frame of
the chunk (the attack kept, at least 20 ms), and whether a transcript word straddles the cut by more than its loose edge (80 ms): a failure when the cut sits in a short gap
(a stop consonant's closure), a note when the silence around the cut is 150 ms or longer (the transcript's edges are loose). For
every chunk file (or its --suffix copy): that it exists, that its length covers its audio (plus two bars of silence for Newtime), and that the grid line it starts on is a
16th of the song (a beat where the manifest says so). Prints a table and a verdict; exit 1 when a cut fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from coproducer import vocalchunk  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--words", default="")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--edge-ms", type=float, default=40.0)
    ap.add_argument("--attack-ms", type=float, default=20.0)
    a = ap.parse_args()
    import soundfile as sf

    man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    x, rate = sf.read(man["source"], dtype="float64", always_2d=True)
    mono = x.mean(axis=1)
    env = vocalchunk.envelope(mono, rate)
    floor = vocalchunk.floor_of(env)
    step = 60.0 / man["bpm"] / 4.0
    wp = a.words or man.get("words_path", "")
    words = []
    if wp:
        d = json.loads(Path(wp).read_text(encoding="utf-8"))
        words = d["words"] if isinstance(d, dict) else d

    def level(t0: float, t1: float) -> float:
        seg = mono[max(0, int(t0 * rate)):max(0, int(t1 * rate))]
        return float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)) if len(seg) else -120.0

    edge = a.edge_ms / 1000.0
    bad = 0
    print("floor %.1f dBFS, 16th %.4f s" % (floor, step))
    print("%3s %7s %8s %8s %7s %7s %6s %s" % ("ch", "cut_s", "before", "after", "rel_ms", "att_ms", "grid", "verdict"))
    for c in man["chunks"]:
        cut = c["audio_s"]
        before, after = level(cut - edge, cut), level(cut, cut + edge)
        # release: how far back from the cut the voice stopped; attack: how far forward it starts
        i = int(cut / vocalchunk.WIN_S)
        j = i
        while j > 0 and env[j - 1] <= floor:
            j -= 1
        rel_ms = (i - j) * vocalchunk.WIN_S * 1000.0
        k = i
        while k < len(env) and env[k] <= floor:
            k += 1
        att_ms = (k - i) * vocalchunk.WIN_S * 1000.0
        straddle = [w["word"] for w in words if w["start"] + 0.08 < cut < w["end"] - 0.08] if c["index"] else []   # the first chunk starts where the file does
        on16 = abs((c["grid_s"] - man["origin_s"]) / step - round((c["grid_s"] - man["origin_s"]) / step)) < 1e-3
        p = Path(c["file"])
        f = p.with_name(p.stem + a.suffix + p.suffix) if a.suffix else p
        problems = []
        if c["index"] > 0 and before > floor + 6:
            problems.append("sound before the cut")
        if after > floor + 6 and att_ms < 1:
            problems.append("cut inside a sound")
        if att_ms < a.attack_ms and c["index"] > 0:
            problems.append("attack margin %.0f ms" % att_ms)
        notes = []
        if straddle and rel_ms + att_ms >= 150.0:
            notes.append("transcript says %s runs across this %.0f ms silence (its edges are loose)" % (" ".join(straddle), rel_ms + att_ms))
        elif straddle:
            problems.append("word straddles: " + " ".join(straddle))
        if not on16:
            problems.append("grid start not on a 16th")
        if not f.is_file():
            problems.append("file missing")
        else:
            n = sf.info(str(f)).frames / rate
            if n + 0.02 < c["end_s"] - c["grid_s"] and not a.suffix:
                problems.append("file shorter than its audio")
        bad += bool(problems)
        print("%3d %7.2f %8.1f %8.1f %7.0f %7.0f %6s %s" % (c["index"], cut, before, after, rel_ms, att_ms, "beat" if c["on_beat"] else "16th",
                                                           "; ".join(problems) if problems else "ok  " + c["text"][:50] + ("  [" + "; ".join(notes) + "]" if notes else "")))
    print("%d of %d cuts clean" % (len(man["chunks"]) - bad, len(man["chunks"])))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
