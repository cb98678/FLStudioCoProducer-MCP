"""One mix iteration on the live project: check the targeted slots are audible, apply edits, save, render. Run on the machine with FL, from the repo root.

    python tools/mix_iter.py ITER.json

ITER.json: {"project": "C:\\\\...\\\\x.flp", "out_dir": "C:\\\\...\\\\render_i27", "edits": [{"module": "set_eq_db_verified", "args": {...}}], "allow_bypassed": false}
Edits to a bypassed effect slot are refused (their readback says verified but nothing changes). Prints one JSON object: warnings, per-edit results and the render path.
Then stage the WAV and run tools/mix_compare.py against the previous render.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import mixtools  # noqa: E402
from coproducer.servers.common import attach_bridge, make_session  # noqa: E402


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    s = make_session(Path(".").resolve(), "mix_iter", "fl-bridge", "A2")
    warn = attach_bridge(s, "coproducer-in", "coproducer-out")
    if warn:
        print(json.dumps({"bridge": warn}))
        return 1
    call = s.registry.call
    tracks = sorted({e["args"].get("index") for e in spec["edits"] if e["module"] in mixtools.SLOT_EDIT_MODULES and e["args"].get("index") is not None})
    states = {}
    for t in tracks:
        r = call("list_effect_slots", index=t)
        states[t] = r.value["slots"] if r.ok else []
    warnings = mixtools.bypassed_edit_warnings(spec["edits"], states)
    out: dict = {"warnings": warnings, "edits": []}
    if warnings and not spec.get("allow_bypassed"):
        out["stopped"] = "edits target bypassed or missing slots; nothing was changed"
        print(json.dumps(out, indent=1))
        return 2
    for e in spec["edits"]:
        r = call(e["module"], **e["args"])
        out["edits"].append({"module": e["module"], "ok": r.ok, "value": r.value if r.ok else r.error.message})
        if not r.ok:
            out["stopped"] = "edit failed"
            print(json.dumps(out, indent=1, default=str))
            return 3
    for m, args in (("save_sandbox_project", {"project": spec["project"]}),
                    ("render_with_restart", {"project": spec["project"], "out_dir": spec["out_dir"], "wait_s": spec.get("wait_s", 240)})):
        r = call(m, **args)
        out[m] = r.value if r.ok else r.error.message
        if not r.ok:
            out["stopped"] = m + " failed"
            print(json.dumps(out, indent=1, default=str))
            return 4
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
