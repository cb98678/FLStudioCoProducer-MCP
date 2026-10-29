"""Measure two renders and print the headline numbers side by side with the change, optionally with a bar-matched spectrum check. Run from the repo root.

    python tools/mix_compare.py BEFORE.wav AFTER.wav [--ref REF.wav --bar-map MAP.json --last-bar 58]

The WAV paths may contain a drive colon; they are copied to a clean temp path first because the measure rules reject it.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from coproducer import mixtools  # noqa: E402
from coproducer.servers.common import make_session  # noqa: E402


def measure(session, path: str) -> dict:
    tmp = Path(tempfile.mkdtemp()) / "m.wav"
    shutil.copyfile(path, tmp)
    r = session.registry.call("build_measure_report", path=str(tmp))
    if not r.ok:
        raise SystemExit("measure failed for %s: %s" % (path, r.error.message))
    v = r.value
    return {"lufs": v["loudness"]["lufs"], "tp": v["true_peak"]["true_peak_dbtp"], "crest": v["crest"]["crest_db"],
            "centroid": v["centroid"]["centroid_hz"], "bands": v["bands"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--ref")
    ap.add_argument("--bar-map")
    ap.add_argument("--last-bar", type=int, default=10**6)
    a = ap.parse_args()
    s = make_session(Path(".").resolve(), "mix_compare", "m", "A2")
    A, B = measure(s, a.before), measure(s, a.after)
    d = mixtools.headline_delta(A, B)
    print("%-12s %10s %10s %8s" % ("", "before", "after", "change"))
    for k in ("lufs", "tp", "crest", "centroid"):
        print("%-12s %10.2f %10.2f %+8.2f" % (k, A[k], B[k], d[k]))
    for k in A["bands"]:
        print("%-12s %10.2f %10.2f %+8.2f" % (k, A["bands"][k], B["bands"][k], d["band_" + k]))
    if a.ref and a.bar_map:
        for label, path in (("before", a.before), ("after", a.after)):
            print("\n-- %s against the reference (bar matched) --" % label)
            subprocess.run([sys.executable, str(REPO / "tools" / "spec_match.py"), path, a.ref, a.bar_map, "--last-bar", str(a.last_bar)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
