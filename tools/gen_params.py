"""Read or set generator-plugin parameters on a channel (global index), printing the display text after each change.

    python tools/gen_params.py CH get 22 328 329
    python tools/gen_params.py CH set 22=0.5 328=0.3
    python tools/gen_params.py CH find "Pitch envelope"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import attach_bridge, make_session  # noqa: E402


def main() -> int:
    s = make_session(Path(".").resolve(), "gen_params", "fl-bridge", "A2")
    warn = attach_bridge(s, "coproducer-in", "coproducer-out")
    if warn:
        print(json.dumps({"bridge": warn})); return 1
    c = lambda n, **kw: s.registry.call(n, **kw)
    ch = int(sys.argv[1]); cmd = sys.argv[2]
    def show(i):
        n = c("op_plugins_get_param_name", paramIndex=i, index=ch, slotIndex=-1, useGlobalIndex=True)
        v = c("op_plugins_get_param_value", paramIndex=i, index=ch, slotIndex=-1, useGlobalIndex=True)
        t = c("op_plugins_get_param_value_string", paramIndex=i, index=ch, slotIndex=-1, useGlobalIndex=True)
        print(i, n.value if n.ok else n.error, "|", t.value if t.ok else t.error, "|", v.value if v.ok else v.error)
    if cmd == "get":
        for a in sys.argv[3:]: show(int(a))
    elif cmd == "set":
        for a in sys.argv[3:]:
            i, val = a.split("=")
            w = c("op_plugins_set_param_value", value=float(val), paramIndex=int(i), index=ch, slotIndex=-1, useGlobalIndex=True)
            print("set", i, val, "ok" if w.ok else w.error); show(int(i))
    elif cmd == "find":
        cnt = c("op_plugins_get_param_count", index=ch, slotIndex=-1, useGlobalIndex=True).value
        for i in range(cnt):
            n = c("op_plugins_get_param_name", paramIndex=i, index=ch, slotIndex=-1, useGlobalIndex=True)
            if n.ok and sys.argv[3].lower() in n.value.lower(): show(i)
    return 0


if __name__ == "__main__":
    sys.exit(main())
