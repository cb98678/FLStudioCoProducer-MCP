"""Measure one WAV with the standard report and print the headline numbers. Run from the repo root.

    python tools/quick_measure.py path.wav
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import make_session  # noqa: E402


def main() -> int:
    src = Path(sys.argv[1])
    tmp = Path(tempfile.mkdtemp()) / "m.wav"      # the path rules reject ':' in the staged name
    shutil.copyfile(src, tmp)
    s = make_session(Path(".").resolve(), "quick_measure", "m", "A2")
    r = s.registry.call("build_measure_report", path=str(tmp))
    if not r.ok:
        print(json.dumps(r.error.message))
        return 1
    v = r.value
    print(json.dumps({"lufs": v["loudness"]["lufs"], "tp": v["true_peak"]["true_peak_dbtp"], "lra": v["range"]["lra_lu"],
                      "crest": v["crest"]["crest_db"], "corr": v["correlation"]["correlation"], "lowmono": v["low_end_mono"]["side_over_mid_db"],
                      "bands": v["bands"], "centroid": v["centroid"]["centroid_hz"], "clipped": v["clipping"]["clipped_samples"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
