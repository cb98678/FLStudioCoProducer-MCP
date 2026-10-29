"""Make render copies of the FL demo projects: the same file with every slot of a plugin this FL edition lacks (config fl.not_owned) emptied,
saved under an ASCII file name in sandbox/demo_study/render. The originals in sandbox/demo_study/flp are not touched.

    .venv\\Scripts\\python.exe tools\\demo_study\\render_prep.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from coproducer import anatomy, flpfile  # noqa: E402
from coproducer.config import load_config  # noqa: E402

src, dst = ROOT / "sandbox" / "demo_study" / "flp", ROOT / "sandbox" / "demo_study" / "render"
dst.mkdir(parents=True, exist_ok=True)
not_owned = set(load_config(ROOT)["fl"].get("not_owned", []))
index = {}
for p in sorted(src.glob("*.flp")):
    slug = re.sub(r"[^A-Za-z0-9]+", "_", p.stem.encode("ascii", "ignore").decode()).strip("_")[:60]
    f = flpfile.Flp.load(p)
    removed = []
    for ins in anatomy.inserts(f):
        for s in ins["slots"]:
            if s["plugin"] in not_owned:
                removed.append((ins["index"], s["slot"], f.remove_slot_plugin(ins["index"], s["slot"])))
    (dst / (slug + ".flp")).write_bytes(f.to_bytes())          # removing whole events is safe in any FL version; save() refuses FL < 21 for patching
    index[slug] = {"source": p.name, "removed": removed}
    print(slug, removed)
(dst.parent / "render_index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
