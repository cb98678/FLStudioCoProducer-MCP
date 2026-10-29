"""Measure where the high-pass filter sweep should rest: produce one project per rest value (the same build, recipe and key), render each
while FL is closed, and report the DC offset held after the song ends, the render length, and the sub and bass level in each drop against the
first value. A rest that leaves no held offset and keeps the sub within 0.5 dB is the answer for transitions.FILTER_REST.

    python tools/calibrate_filter_rest.py BUILT.flp PLAN.json --recipe club_house --key A --work sandbox\\diag\\filter_rest --rest 0 0.01 0.03 0.06
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

from coproducer import dsp, transitions  # noqa: E402
from coproducer.servers.common import make_session  # noqa: E402

HOME = Path(__file__).resolve().parents[1]


def measure(wav: str, plan: dict) -> dict:
    x, sr = sf.read(wav, dtype="float64", always_2d=True)
    bar = 240.0 / float(plan["bpm"])
    end = plan["sections"][-1]["end"] * bar
    after = x[int((end + 2.0) * sr):]
    drops = []
    for sec in plan["sections"]:
        if sec["name"] == "drop":
            seg = x[int(sec["start"] * bar * sr): int(sec["end"] * bar * sr)]
            drops.append(dsp.band_energy_db(seg, sr, {"sub": (20, 60), "bass": (60, 250)}) | {"rms_db": round(dsp.db(float(np.sqrt((seg ** 2).mean()))), 2)})
    return {"seconds": round(len(x) / sr, 2), "expected_s": round(end, 2), "held_dc": [round(float(v), 5) for v in (after.mean(axis=0) if len(after) else [0, 0])],
            "drops": drops}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("built")
    ap.add_argument("plan")
    ap.add_argument("--recipe", default="club_house")
    ap.add_argument("--key", default="A")
    ap.add_argument("--work", required=True)
    ap.add_argument("--rest", type=float, nargs="+", default=[0.0, 0.01, 0.03, 0.06])
    a = ap.parse_args()
    s = make_session(HOME, "calibrate_filter_rest", "fl-bridge", "A2")
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    work = Path(a.work)
    rows = []
    for v in a.rest:
        transitions.FILTER_REST = v
        tag = "rest_%03d" % round(v * 1000)
        out = work / (tag + ".flp")
        r = s.registry.call("apply_production_recipe", project=a.built, out_project=str(out), recipe=a.recipe, key=a.key)
        if not r.ok:
            print(tag, r.error.code, r.error.message)
            return 1
        r = s.registry.call("render_via_cli", project=str(out), out_dir=str(work / tag), timeout_s=1200)
        if not r.ok:
            print(tag, r.error.code, r.error.message)
            return 1
        row = {"rest": v, **measure(r.value["path"], plan)}
        rows.append(row)
        print(json.dumps(row), flush=True)
    base = rows[0]["drops"]
    for row in rows:
        row["sub_change_db"] = [round(d["sub"] - b["sub"], 2) for d, b in zip(row["drops"], base)]
    (work / "filter_rest.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for row in rows:
        print("rest %.3f  length %.2f s (plan %.2f)  held dc %s  sub change %s" % (row["rest"], row["seconds"], row["expected_s"], row["held_dc"], row["sub_change_db"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
