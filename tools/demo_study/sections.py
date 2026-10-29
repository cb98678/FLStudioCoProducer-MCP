"""The sections of every studied demo song (from docs/demo_study/data, tools/demo_study/data.py) as the measure step reads them:
sandbox/demo_study/sections.json, {song: {"bpm", "bars", "sections": [{"start_bar", "bars", "name", "energy"}]}}.

    python tools/demo_study/sections.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out = {}
for p in sorted((ROOT / "docs" / "demo_study" / "data").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    out[p.stem] = {"bpm": d["bpm"], "bars": d["bars"], "sections": [{k: s[k] for k in ("start_bar", "bars", "name", "energy")} for s in d["sections"]]}
dst = ROOT / "sandbox" / "demo_study" / "sections.json"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
print(len(out), "songs to", dst)
