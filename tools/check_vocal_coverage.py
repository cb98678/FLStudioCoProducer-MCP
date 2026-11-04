"""Is every line of the song in the remix? Maps the vocal channel's playlist clips of a built remix back to the song's own clock (the
stretched vocal file's content windows, the stretch and its measured delay undone), then checks every transcribed word lies inside a clip,
none plays twice, the clips run in the song's order, and what the clips leave out of the voice is silence (its loudest 20 ms).

    python tools/check_vocal_coverage.py --work sandbox\\remix\\NAME --words sandbox\\songs\\SONG\\vocal_words.json [--vocals VOCALS.wav]

A word listed as missing whose gap is quiet (under about -40 dBFS) is a transcription time stretched across a pause, not a lost line.
Exit code 1 when a gap holds sound or a word plays twice. Only reads.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import flpfile  # noqa: E402

QUIET_DBFS = -40.0


def clip_spans(f: flpfile.Flp, stretch: float, delay_s: float, fl_stretch: bool = False) -> list[tuple[float, float, float]]:
    """(song start s, song end s, remix bar) of each vocal clip, in playlist order. With FL's own stretching on the channel the clip's
    window is already in the song's own milliseconds."""
    voc = {c for c in f.channel_ids() if (f.channel_info(c)["name"] or "").lower().startswith("vocal")}
    clips = sorted((a for a in f.audio_clips() if a["channel"] in voc), key=lambda a: a["pos"])
    if fl_stretch:
        return [(a["start_ms"] / 1000, a["end_ms"] / 1000, a["pos"] / flpfile.TICKS_PER_BAR) for a in clips]
    return [((a["start_ms"] / 1000 - delay_s) * stretch, (a["end_ms"] / 1000 - delay_s) * stretch, a["pos"] / flpfile.TICKS_PER_BAR) for a in clips]


def coverage(spans: list[tuple[float, float, float]], words: list[dict], slack_s: float = 0.05) -> dict:
    """Words outside every clip (missing), inside two or more (twice), and whether the clips play in the song's order."""
    missing, twice = [], []
    for i, w in enumerate(words):
        mid = 0.5 * (w["start"] + w["end"])
        n = sum(1 for a, b, _r in spans if a - slack_s <= mid <= b + slack_s)
        (missing if n == 0 else twice if n > 1 else []).append({"index": i, "start": round(w["start"], 2)})
    return {"words": len(words), "missing": missing, "twice": twice, "in_order": all(spans[k][0] <= spans[k + 1][0] for k in range(len(spans) - 1))}


def gaps(spans: list[tuple[float, float, float]], end_s: float) -> list[tuple[float, float]]:
    """The stretches of the song's voice no clip plays: before the first, between clips and after the last. Clips that repeat or overlap
    a passage (a hook in every drop, a throw under a phrase) are merged first, so only the song's own time with no clip at all counts."""
    merged: list[list[float]] = []
    for a, b in sorted((a, b) for a, b, _r in spans):
        if merged and a <= merged[-1][1] + 0.02:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    edges = [(0.0, 0.0)] + [(a, b) for a, b in merged] + [(end_s, end_s)]
    return [(b0, a1) for (_a0, b0), (a1, _b1) in zip(edges, edges[1:]) if a1 - b0 > 0.02]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="", help="a remix_song work folder (its remix_report.json names the project, its audio folder the stretch)")
    ap.add_argument("--flp", default="", help="instead of --work: a project whose vocal channels play the song's file on FL's own Stretch")
    ap.add_argument("--words", required=True)
    ap.add_argument("--vocals", default="")
    a = ap.parse_args()
    if a.flp:
        f = flpfile.Flp.load(a.flp)
        spans = clip_spans(f, 1.0, 0.0, True)
    else:
        work = Path(a.work)
        rep = json.loads((work / "remix_report.json").read_text(encoding="utf-8"))
        meta = json.loads((work / "audio" / "techhouse_audio.json").read_text(encoding="utf-8"))
        flp = Path(rep["final_project"])
        f = flpfile.Flp.load(str(flp if flp.is_absolute() else HOME / flp))
        spans = clip_spans(f, float(meta["stretch"]), float(meta.get("delay_s", 0.0)), bool(meta.get("fl_stretch")))
    words = json.loads(Path(a.words).read_text(encoding="utf-8"))
    words = words["words"] if isinstance(words, dict) else words
    out = {"clips": [[round(x, 2) for x in s] for s in spans], **coverage(spans, words)}
    loud = []
    if a.vocals:
        import numpy as np
        import soundfile as sf
        x, sr = sf.read(a.vocals, always_2d=True)
        m = x.mean(axis=1)
        h = int(0.02 * sr)
        for b0, a1 in gaps(spans, len(m) / sr):
            seg = m[int(b0 * sr):int(a1 * sr)]
            top = max(20 * np.log10(np.sqrt(np.mean(seg[i:i + h] ** 2)) + 1e-9) for i in range(0, max(1, len(seg) - h), h))
            loud.append({"from": round(b0, 2), "to": round(a1, 2), "loudest_dbfs": round(float(top), 1)})
        out["left_out"] = loud
    print(json.dumps(out, indent=1))
    return 1 if out["twice"] or any(g["loudest_dbfs"] > QUIET_DBFS for g in loud) else 0


if __name__ == "__main__":
    sys.exit(main())
