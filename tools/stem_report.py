"""Measure every stem in a folder and print one JSON report: loudness, crest, spectrum, stereo, share of the total, tempo and key.

    python tools/stem_report.py <stems folder> <out.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import make_session  # noqa: E402


def main() -> int:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    s = make_session(Path(".").resolve(), "stem_report", "m", "A2")
    rep = {}
    for wav in sorted(folder.glob("*.wav")):
        r = s.registry.call("build_measure_report", path=str(wav))
        if not r.ok:
            rep[wav.stem] = {"error": r.error.message}
            continue
        v = r.value
        row = {"lufs": v["loudness"]["lufs"], "tp": v["true_peak"]["true_peak_dbtp"], "crest": v["crest"]["crest_db"],
               "rms_db": v["rms"]["rms_db"], "centroid_hz": v["centroid"]["centroid_hz"], "bands": v["bands"],
               "corr": v.get("correlation", {}).get("correlation"), "silent_fraction": v["silence"]["silent_fraction"]}
        for op, key in (("estimate_bpm_dsp", "bpm"), ("estimate_key_dsp", "key")):
            a = s.registry.call(op, path=str(wav))
            row[key] = ({"bpm": a.value["bpm"], "ambiguous": a.value.get("ambiguous")} if key == "bpm" else
                        {"key": a.value["key"], "margin": a.value["margin"]}) if a.ok else {"error": a.error.message}
        rep[wav.stem] = row
    out.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
