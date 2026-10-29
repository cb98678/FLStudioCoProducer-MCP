"""Measure every audio file in a folder (loudness, crest, spectrum) and write one JSON report. Read-only.

    python tools/sample_survey.py <folder> <out.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import make_session  # noqa: E402

EXT = {".wav", ".flac", ".ogg", ".mp3", ".wv"}


def main() -> int:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    s = make_session(Path(".").resolve(), "sample_survey", "m", "A2")
    rep = {}
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in EXT:
            continue
        try:
            info = sf.info(str(f))
        except Exception as e:  # noqa: BLE001 - any unreadable file is reported, not fatal
            rep[f.name] = {"error": str(e)[:80]}
            continue
        row = {"seconds": round(info.duration, 2), "channels": info.channels}
        r = s.registry.call("build_measure_report", path=str(f))
        if r.ok:
            v = r.value
            row.update({"lufs": v["loudness"]["lufs"], "crest": v["crest"]["crest_db"], "tp": v["true_peak"]["true_peak_dbtp"],
                        "centroid_hz": v["centroid"]["centroid_hz"], "bands": v["bands"]})
        else:
            row["error"] = r.error.message[:80]
        rep[f.name] = row
    out.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print("wrote", out, len(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
