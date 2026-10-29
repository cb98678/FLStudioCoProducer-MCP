"""List every channel (all rack groups) through the live bridge, or mute/unmute some by global index.

    python tools/chan_global.py list OUT.json
    python tools/chan_global.py mute 2 3 4 5
    python tools/chan_global.py unmute 2 3 4 5

Channel API reads use globalCount/useGlobalIndex so channels in other rack groups are included.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import attach_bridge, make_session  # noqa: E402


def main() -> int:
    s = make_session(Path(".").resolve(), "chan_global", "fl-bridge", "A2")
    warn = attach_bridge(s, "coproducer-in", "coproducer-out")
    if warn:
        print(json.dumps({"bridge": warn}))
    c = lambda name, **kw: s.registry.call(name, **kw)
    cmd = sys.argv[1]
    if cmd == "list":
        n = c("op_channels_channel_count", globalCount=True)
        rows = []
        for i in range(n.value):
            r = {"gindex": i}
            for k, op in (("name", "op_channels_get_channel_name"), ("type", "op_channels_get_channel_type"),
                          ("muted", "op_channels_is_channel_muted"), ("track", "op_channels_get_target_fx_track"),
                          ("volume", "op_channels_get_channel_volume")):
                g = c(op, index=i, useGlobalIndex=True)
                r[k] = g.value if g.ok else "ERR " + str(g.error)
            rows.append(r)
        Path(sys.argv[2]).write_text(json.dumps({"count": n.value, "rows": rows}, indent=1))
        print("channels", n.value)
    elif cmd == "vol":
        for a in sys.argv[2:]:
            i, v = a.split("=")
            w = c("op_channels_set_channel_volume", index=int(i), volume=float(v), useGlobalIndex=True)
            r = c("op_channels_get_channel_volume", index=int(i), useGlobalIndex=True)
            print(i, "set", v, "ok" if w.ok else w.error, "read", r.value if r.ok else r.error)
    else:
        val = 1 if cmd == "mute" else 0
        for a in sys.argv[2:]:
            w = c("op_channels_mute_channel", index=int(a), value=val, useGlobalIndex=True)
            r = c("op_channels_is_channel_muted", index=int(a), useGlobalIndex=True)
            print(a, "wrote", val, "ok" if w.ok else w.error, "read", r.value if r.ok else r.error)
    return 0


if __name__ == "__main__":
    sys.exit(main())
