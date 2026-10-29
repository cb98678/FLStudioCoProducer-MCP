"""Read the whole open FL project through the bridge and write one JSON file: mixer inserts (name, colour, level, pan, width, routes,
every effect slot with every parameter's text and raw value, slot mix and mute), and channels (name, type, level, pan, target insert,
generator parameters). Read-only: a thin wrapper that runs the module snapshot_project_params and writes its result.

    python tools/dump_project_live.py OUT.json [--inserts 0-21,100] [--max-params 400] [--no-channel-params]

OUT.json must sit under a folder named sandbox.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import attach_bridge, make_session  # noqa: E402


def _ranges(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--inserts", default="0-21,100")
    ap.add_argument("--max-params", type=int, default=400)
    ap.add_argument("--no-channel-params", action="store_true")
    a = ap.parse_args()
    if "sandbox" not in [p.lower() for p in Path(a.out).resolve().parts]:
        sys.exit("refusing %s: output must be under a folder named sandbox" % a.out)
    s = make_session(Path(".").resolve(), "dump_project_live", "fl-bridge", "A2")
    warn = attach_bridge(s, "coproducer-in", "coproducer-out")
    if warn:
        print(json.dumps({"bridge": warn}))
        return 1
    began = time.time()
    r = s.registry.call("snapshot_project_params", inserts=_ranges(a.inserts), max_params=a.max_params, channel_params=not a.no_channel_params)
    if not r.ok:
        print(json.dumps({"error": r.error.message}))
        return 1
    data = dict(r.value, stats={"seconds": round(time.time() - began, 1)})
    Path(a.out).write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(json.dumps(data["stats"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
