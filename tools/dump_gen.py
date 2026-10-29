"""Print the plugin name and every parameter (name, display value, raw) of generator channels by global index. Read-only.

    python tools/dump_gen.py OUT.json 7 14 16
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import attach_bridge, make_session  # noqa: E402


def main() -> int:
    s = make_session(Path(".").resolve(), "dump_gen", "fl-bridge", "A2")
    warn = attach_bridge(s, "coproducer-in", "coproducer-out")
    if warn:
        print(json.dumps({"bridge": warn})); return 1
    c = lambda n, **kw: s.registry.call(n, **kw)
    out = {}
    for ch in [int(a) for a in sys.argv[2:]]:
        nm = c("op_plugins_get_plugin_name", index=ch, slotIndex=-1, userName=False, useGlobalIndex=True)
        cnt = c("op_plugins_get_param_count", index=ch, slotIndex=-1, useGlobalIndex=True)
        row = {"channel": ch, "plugin": nm.value if nm.ok else str(nm.error), "count": cnt.value if cnt.ok else None, "params": []}
        if cnt.ok:
            for p in range(min(cnt.value, 400)):
                n = c("op_plugins_get_param_name", paramIndex=p, index=ch, slotIndex=-1, useGlobalIndex=True)
                v = c("op_plugins_get_param_value", paramIndex=p, index=ch, slotIndex=-1, useGlobalIndex=True)
                t = c("op_plugins_get_param_value_string", paramIndex=p, index=ch, slotIndex=-1, useGlobalIndex=True)
                row["params"].append({"i": p, "name": n.value if n.ok else None, "raw": v.value if v.ok else None, "text": t.value if t.ok else None})
        out[ch] = row
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    print("dumped", list(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
