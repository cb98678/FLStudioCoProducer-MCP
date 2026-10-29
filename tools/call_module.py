"""Call one module against the live machine (real FL bridge and desktop) and print the Result as JSON.

    python tools/call_module.py list_open_dialogs
    python tools/call_module.py load_plugin_gui '{"name": "Fruity Limiter"}' --no-bridge
    python tools/call_module.py write_song_notes @sandbox\\songs\\NAME\\notes_args.json --no-bridge

Use it to try a single module by hand. Writing modules stay under the same autonomy and sandbox rules as in a run (ceiling A2).
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
    ap.add_argument("module")
    ap.add_argument("args", nargs="?", default="{}")
    ap.add_argument("--home", default=".")
    ap.add_argument("--allow-unverified", action="store_true", help="let a draft GUI recipe run once, to try it on this machine")
    ap.add_argument("--no-bridge", action="store_true", help="do not open the MIDI bridge (desktop-only modules)")
    a = ap.parse_args()
    s = make_session(Path(a.home).resolve(), "call_module", "fl-bridge", "A2")
    if a.allow_unverified:
        from coproducer.services import get_service
        get_service("desktop_config")["allow_unverified"] = True
    s.collab = type("Yes", (), {"approve": lambda self, w, d: __import__("coproducer.result", fromlist=["ok"]).ok(True),
                                "ask": lambda self, q, o: __import__("coproducer.result", fromlist=["fail"]).fail("E_PENDING_HUMAN", q)})()
    if not a.no_bridge:
        warn = attach_bridge(s, "coproducer-in", "coproducer-out")
        if warn:
            print(json.dumps({"bridge": warn}))
    raw = Path(a.args[1:]).read_text(encoding="utf-8") if a.args.startswith("@") else a.args  # @FILE.json: the arguments from a file (no shell quoting)
    res = s.registry.call(a.module, **json.loads(raw))
    print(json.dumps(res.to_dict(), indent=1, default=str))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
