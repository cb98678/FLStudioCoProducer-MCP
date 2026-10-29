"""Print every effect slot on one mixer track: plugin name, then each parameter with its display value. Read-only.

    python tools/dump_chain.py 0 [--slots 10]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import attach_bridge, make_session  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("track", type=int)
    ap.add_argument("--slots", type=int, default=10)
    ap.add_argument("--only", type=int, default=-1, help="dump just this slot")
    a = ap.parse_args()
    s = make_session(Path(".").resolve(), "dump_chain", "fl-bridge", "A2")
    warn = attach_bridge(s, "coproducer-in", "coproducer-out")
    if warn:
        print(json.dumps({"bridge": warn}))
        return 1
    out = []
    for slot in ([a.only] if a.only >= 0 else range(a.slots)):
        n = s.registry.call("op_plugins_get_plugin_name", index=a.track, slotIndex=slot, userName=False)
        u = s.registry.call("op_plugins_get_plugin_name", index=a.track, slotIndex=slot, userName=True)
        if not n.ok:
            out.append({"slot": slot, "error": n.error.message})
            continue
        row = {"slot": slot, "plugin": n.value, "user_name": u.value if u.ok else None, "params": {}}
        lp = s.registry.call("list_plugin_params", index=a.track, slot_index=slot, limit=200)
        if lp.ok:
            for p in lp.value["params"]:
                v = s.registry.call("op_plugins_get_param_value_string", paramIndex=p["param"], index=a.track, slotIndex=slot)
                raw = s.registry.call("op_plugins_get_param_value", paramIndex=p["param"], index=a.track, slotIndex=slot)
                row["params"][p["name"]] = {"i": p["param"], "text": v.value if v.ok else None, "raw": round(raw.value, 4) if raw.ok else None}
        out.append(row)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
