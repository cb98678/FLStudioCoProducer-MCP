"""Find which part of a project puts a DC offset on the output: render every mixer track solo (split_part_projects, render_folder_via_cli) and
report each solo render's DC per channel over the whole file and over its last two seconds, and its length. Only while FL Studio is closed.

    python tools/dc_probe.py PROJECT.flp --work sandbox\\diag\\NAME [--bypass-master]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

from coproducer.servers.common import make_session  # noqa: E402

HOME = Path(__file__).resolve().parents[1]


def dc_row(path: Path) -> dict:
    x, sr = sf.read(str(path), dtype="float64", always_2d=True)
    tail = x[-2 * sr:] if len(x) > 2 * sr else x
    return {"file": path.name, "seconds": round(len(x) / sr, 2), "dc": [round(float(v), 5) for v in x.mean(axis=0)],
            "tail_dc": [round(float(v), 5) for v in tail.mean(axis=0)], "tail_ac_db": round(float(20 * np.log10(tail.std(axis=0).max() + 1e-12)), 1),
            "peak_db": round(float(20 * np.log10(np.abs(x).max() + 1e-12)), 1)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--work", required=True)
    ap.add_argument("--bypass-master", action="store_true")
    a = ap.parse_args()
    s = make_session(HOME, "dc_probe", "fl-bridge", "A2")
    work = Path(a.work)
    r = s.registry.call("split_part_projects", project=a.project, out_dir=str(work / "parts"), bypass_master=a.bypass_master)
    if not r.ok:
        print(r.error.code, r.error.message)
        return 1
    r = s.registry.call("render_folder_via_cli", folder=str(work / "parts"), out_dir=str(work / "renders"), timeout_s=3600)
    if not r.ok:
        print(r.error.code, r.error.message)
        return 1
    rows = [dc_row(p) for p in sorted((work / "renders").glob("*.wav"))]
    rows.sort(key=lambda row: -max(abs(v) for v in row["tail_dc"]))
    (work / "dc_probe.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for row in rows:
        print("%-44s %7.2fs dc %-20s tail %-20s tail_ac %6.1f dB" % (row["file"], row["seconds"], row["dc"], row["tail_dc"], row["tail_ac_db"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
