"""Put the vocal clips of an FL project in line with the grid without cutting a word (skill vocal-slice-align, 2026-11-02).

    python tools/align_vocal_clips.py PROJECT.flp --vocal-file VOCAL.wav --source-bpm 86 --origin 0.0755 --samples-dir FOLDER
        [--mixer-rows 10=1,16=2] [--mixer-channels 10=24,16=30] [--lead auto] [--out ALIGNED.flp] [--report align.json]

The vocal channels are every channel whose sample is VOCAL.wav or a slice of it (a file whose first half second is found in VOCAL.wav by
cross-correlation; FL's slice tool writes "NAME - Part_n.wav"). Reads the onsets (newtimeview.onset_times) and her lead
(newtimeview.best_lead), then coproducer.vocalalign decides: phrases to her beat grid (plus the lead), riffs by their first onset to the
nearest 16th, throws with their phrase, duplicates and flams gone, contiguous slices rejoined. Without --out it only reports. With --out the
clips are rewritten on one channel and one playlist row per mixer track (--mixer-channels, --mixer-rows; defaults: the first vocal channel
on each mixer track, and the row of its first clip). Other channels, notes and automation are untouched; the clone channels left without
clips stay for the caller to remove (flpfile.remove_channel).
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import flpfile, newtimeview, vocalalign  # noqa: E402


def locate(long: np.ndarray, part: np.ndarray, sr: int) -> tuple[float, float]:
    """Where a slice file starts in the long file (seconds) and how well it matches (1.0 = identical samples)."""
    seg = part[:int(0.5 * sr)]
    n = 1
    while n < len(long) + len(seg):
        n <<= 1
    c = np.fft.irfft(np.fft.rfft(long, n) * np.conj(np.fft.rfft(seg, n)))[:len(long)]
    k = int(np.argmax(c))
    denom = float(np.linalg.norm(seg) * np.linalg.norm(long[k:k + len(seg)])) + 1e-9
    return k / sr, round(float(c[k] / denom), 3)


def read_mono(path: str) -> tuple[np.ndarray, int]:
    y, sr = sf.read(path, always_2d=True)
    return y.mean(axis=1), sr


def parse_map(s: str) -> dict[int, int]:
    return {int(a): int(b) for a, b in (x.split("=") for x in s.split(",") if x.strip())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--vocal-file", required=True)
    ap.add_argument("--source-bpm", type=float, required=True)
    ap.add_argument("--origin", type=float, default=0.0, help="seconds into the vocal file where her beat 0 falls (warp_to_grid's origin)")
    ap.add_argument("--samples-dir", default="", help="where the project's sample files are when the project points elsewhere (a zip opened from Temp)")
    ap.add_argument("--mixer-rows", default="", help="MIXER=ROW,...: the playlist row for the clips of each mixer track")
    ap.add_argument("--mixer-channels", default="", help="MIXER=CHANNEL,...: the channel that keeps the clips of each mixer track")
    ap.add_argument("--lead", default="auto", help="her lead in seconds, or auto (newtimeview.best_lead on her onsets)")
    ap.add_argument("--phrase-beats", type=float, default=vocalalign.PHRASE_BEATS)
    ap.add_argument("--out", default="")
    ap.add_argument("--report", default="")
    a = ap.parse_args()

    f = flpfile.Flp.load(a.project)
    ppq = f.ppq
    long, sr = read_mono(a.vocal_file)
    vocal_name = os.path.basename(a.vocal_file).lower()
    offsets: dict[int, float] = {}
    mixers: dict[int, int] = {}
    located = {}
    for ch in f.channel_ids():
        info = f.channel_info(ch)
        smp = info.get("sample") or ""
        if not smp:
            continue
        base = os.path.basename(smp)
        if base.lower() == vocal_name:
            offsets[ch] = 0.0
        elif a.samples_dir and os.path.isfile(os.path.join(a.samples_dir, base)) and " - part" in base.lower():
            if base not in located:
                part, psr = read_mono(os.path.join(a.samples_dir, base))
                if psr != sr:
                    raise SystemExit("slice %s has another sample rate" % base)
                located[base] = locate(long, part, sr)
            off, match = located[base]
            if match < 0.98:
                print("slice %s matches the vocal file only %.2f; left alone" % (base, match))
                continue
            offsets[ch] = off
        else:
            continue
        mixers[ch] = int(info.get("track") or 0)
    if not offsets:
        raise SystemExit("no channel plays %s" % vocal_name)
    onsets = newtimeview.onset_times(long, sr)
    lead = newtimeview.best_lead(onsets - a.origin, a.source_bpm) if a.lead == "auto" else float(a.lead)
    clips = vocalalign.collect(f, offsets, mixers)
    clips = vocalalign.dedupe(clips, ppq, a.source_bpm)
    clips = vocalalign.merge_contiguous(clips, a.source_bpm, ppq)
    clips = vocalalign.plan_moves(clips, onsets, a.source_bpm, a.origin, ppq, lead, a.phrase_beats)
    rep = {"project": a.project, "vocal_file": a.vocal_file, "source_bpm": a.source_bpm, "origin_s": a.origin, "lead_s": lead,
           "onsets": len(onsets), "slices": {k: {"origin_s": round(v[0], 4), "match": v[1]} for k, v in located.items()},
           "channels": {str(ch): {"file_offset_s": round(off, 4), "mixer": mixers[ch]} for ch, off in offsets.items()},
           "clips": vocalalign.report(clips, ppq)}
    for r in rep["clips"]:
        print("%-7s ch%-3d mixer %-3d %9.3f -> %-9s shift %+7.3f  win %7.3f..%7.3f  %s" % (
            r["kind"], r["channel"], r["mixer"], r["pos_beats"], ("%.3f" % r["new_pos_beats"]) if r["new_pos_beats"] is not None else "gone",
            r["shift_beats"], r["window_s"][0], r["window_s"][1], r["note"]))
    print("lead %.0f ms; %d onsets" % (lead * 1000, len(onsets)))
    if a.out:
        rows = parse_map(a.mixer_rows)
        chans = parse_map(a.mixer_channels)
        for c in clips:
            rows.setdefault(c.mixer, c.row)
            chans.setdefault(c.mixer, c.channel)
        template = f.audio_item(min(offsets))
        done = vocalalign.apply(f, clips, rows, chans, template, set(offsets))
        f.save(a.out)
        rep["applied"] = {**done, "rows": rows, "channels": chans, "out": a.out}
        print("wrote", a.out, done)
    if a.report:
        Path(a.report).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
