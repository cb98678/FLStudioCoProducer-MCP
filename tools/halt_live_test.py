"""G2-5 live check: a GUI recipe is running in FL, you press Ctrl+Alt+F12, the recipe stops at the next action.

Start the key watcher first:   coproducer halt --key        (its own window)
Then run this script. While it prints "action N", press Ctrl+Alt+F12 (or let the person driving the test do it).
The recipe presses Shift (harmless in FL) 16 times, 1.5 seconds apart.
Pass: the result is E_HALTED, fewer than 16 actions were sent, and none were sent after the HALT file appeared.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import halt_key  # noqa: E402
from coproducer.servers.common import make_session  # noqa: E402
from coproducer.services import set_service  # noqa: E402


def main() -> int:
    home = Path(".").resolve()
    halt_key.clear(home)
    s = make_session(home, "halt_live", "fl-bridge", "A2")
    d = Path(tempfile.mkdtemp())
    steps = []
    for _ in range(16):
        steps += [{"do": "hotkey", "keys": ["shift"]}, {"do": "wait", "seconds": 1.5}]
    (d / "halt_demo.json").write_text(json.dumps({"name": "halt_demo", "verified": True, "params": [], "steps": steps}))
    set_service("recipes_dir", str(d))
    halt_file = halt_key.global_halt_file(home)
    after_halt, seen, t0 = [], {"n": 0}, time.time()
    previous = s.registry.observer

    def observer(name, kwargs, res, secs):
        if name == "press_hotkey":
            seen["n"] += 1
            late = halt_file.exists() and res.ok
            print("action %d at t=%.1fs ok=%s%s" % (seen["n"], time.time() - t0, res.ok, "  AFTER HALT" if late else ""), flush=True)
            if late:
                after_halt.append(seen["n"])
        if previous:
            previous(name, kwargs, res, secs)
    s.registry.observer = observer
    print("recipe starting; press Ctrl+Alt+F12 now", flush=True)
    r = s.registry.call("run_gui_recipe", name="halt_demo")
    print(json.dumps({"ok": r.ok, "code": None if r.ok else r.error.code, "stopped_at_step": None if r.ok else r.error.detail.get("step"),
                      "actions_sent": seen["n"], "actions_sent_after_halt": after_halt, "halt_file": halt_file.read_text() if halt_file.exists() else None}), flush=True)
    passed = (not r.ok) and r.error.code == "E_HALTED" and seen["n"] < 16 and not after_halt
    print("G2-5 live:", "PASS" if passed else "FAIL", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
