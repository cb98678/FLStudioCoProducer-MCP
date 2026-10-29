"""Point vocal channels at their cleaned files and fix clip timing in an FLP. Run from the repo root.

    python tools/vocal_patch.py IN.flp OUT.flp --device-dir "C:\\coproducer\\sandbox\\DTP_work\\vc" \
        --reports vc/report_a.json vc/report_b.json [--local-dir DIR] [--bpm 140] [--plan plan.json] [--no-timing]

--reports are the vocal_clean_report.json files that tools/vocal_clean.py wrote. A channel whose sample file name is a key in a
report gets pointed at <device-dir>\\<out>. If region_start_s is not zero the clip offsets of that channel move earlier by it.
--local-dir holds copies of the cleaned wavs (any subset); clips on those files get the timing plan from vocalclips.plan_clip
(trim the lead-in, snap an off-grid onset). Clips on other files only get the file swap.
Sliced-audio copies of one recording (name_2.ogg ... name_9.ogg) are the same file, so any of them maps to the same cleaned file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import vocalclips as V  # noqa: E402
from coproducer.flpfile import EV_SAMPLE_PATH, Flp  # noqa: E402

SLICED = re.compile(r"^(audio_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_\d+\.ogg$")


def lookup(reports: dict, base: str):
    if base in reports:
        return reports[base]
    m = SLICED.match(base)
    if m:
        for k, v in reports.items():
            if SLICED.match(k) and SLICED.match(k).group(1) == m.group(1):
                return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("flp_in")
    ap.add_argument("flp_out")
    ap.add_argument("--device-dir", required=True)
    ap.add_argument("--reports", nargs="+", required=True)
    ap.add_argument("--local-dir")
    ap.add_argument("--bpm", type=float, default=140.0)
    ap.add_argument("--plan")
    ap.add_argument("--no-timing", action="store_true")
    ap.add_argument("--only", help="comma-separated channel indexes: patch just these (for bisecting a bad render)")
    a = ap.parse_args()

    reports: dict = {}
    for r in a.reports:
        reports.update(json.loads(Path(r).read_text()))
    f = Flp.load(a.flp_in)
    only = {int(v) for v in a.only.split(",")} if a.only else None
    chan: dict[int, dict] = {}
    for ch in range(f.channel_count):
        try:
            path = f.get_text(ch, EV_SAMPLE_PATH)
        except Exception:
            continue
        if only is not None and ch not in only:
            continue
        base = path.replace("/", "\\").split("\\")[-1]
        rep = lookup(reports, base)
        if not rep:
            continue
        new = a.device_dir.rstrip("\\") + "\\" + rep["out"]
        f.set_sample(ch, new)
        chan[ch] = {"from": base, "to": rep["out"], "shift_ms": rep["region_start_s"] * 1000.0}

    envs: dict[str, tuple] = {}
    if a.local_dir and not a.no_timing:
        for p in Path(a.local_dir).glob("*_vc.wav"):
            x, sr = sf.read(str(p))
            envs[p.name] = (V.envelope(x.mean(axis=1) if x.ndim > 1 else x, sr), sr)

    plans: list[dict] = []

    def fix(it: bytes) -> bytes:
        d = V.read_item(it)
        c = chan.get(d["ref"])
        if c is None or d["len"] == 0 or d["ref"] >= V.PATTERN_BASE:
            return it
        if c["to"] in envs and not a.no_timing:
            env, sr = envs[c["to"]]
            p = V.plan_clip(it, env, sr, bpm=a.bpm, source_shift_ms=c["shift_ms"])
            if p is not None:
                plans.append({"ch": d["ref"], "bar": d["pos"] / 384.0, "to_bar": p.pos / 384.0, "lag_ms": round(p.lag_ms, 1),
                              "trim_ms": round(p.trimmed_ms, 1), "moved_ticks": p.moved_ticks, "err_ms": round(p.grid_err_ms, 1)})
                return V.write_item(it, pos=p.pos, start_ms=p.start_ms, end_ms=p.end_ms)
        if c["shift_ms"]:
            return V.write_item(it, start_ms=d["start_ms"] - c["shift_ms"], end_ms=d["end_ms"] - c["shift_ms"])
        return it

    changed = f.map_playlist(fix)
    f.save(a.flp_out)
    summary = {"channels_repointed": len(chan), "clips_changed": changed, "clips_trimmed": sum(1 for p in plans if p["trim_ms"] > 0),
               "clips_moved": sum(1 for p in plans if p["moved_ticks"]), "channels": chan}
    print(json.dumps(summary, indent=1))
    if a.plan:
        Path(a.plan).write_text(json.dumps({"summary": summary, "plans": plans}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
