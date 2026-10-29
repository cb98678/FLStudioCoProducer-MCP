"""Run a short list of FL Studio interface steps through the desktop modules (the same primitives GUI recipes use) and finish with a
screenshot: the way to explore an editor before its recipe is written.

    python tools/gui_steps.py STEPS.json

STEPS.json: {"shot": "sandbox/screens/NAME.png", "steps": [{"do": "click", "x": 10, "y": 20, "button": "left", "clicks": 1, "modifiers": ["shift"]},
{"do": "hotkey", "keys": ["ctrl", "o"]}, {"do": "type", "text": "..."}, {"do": "wait", "s": 1.0}, {"do": "drag", "x1":.., "y1":.., "x2":.., "y2":..},
{"do": "shot", "path": "sandbox/screens/mid.png"}, {"do": "dialogs"}, {"do": "recipe", "name": "...", "params": {}}]}
Coordinates are FL window pixels, as in take_screenshot images. It stops at the first failed step and still takes the final screenshot.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer.servers.common import make_session  # noqa: E402
from coproducer.services import get_service  # noqa: E402


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    home = Path(__file__).resolve().parents[1]
    s = make_session(home, "gui_steps", "fl-bridge", "A2")
    if spec.get("allow_unverified"):
        get_service("desktop_config")["allow_unverified"] = True
    call = s.registry.call
    log = []
    for i, st in enumerate(spec.get("steps", [])):
        d = st["do"]
        if d == "click":
            extra = {"modifiers": st["modifiers"]} if st.get("modifiers") else {}
            r = call("click_at", x=int(st["x"]), y=int(st["y"]), button=st.get("button", "left"), clicks=int(st.get("clicks", 1)), **extra)
        elif d == "hotkey":
            r = call("press_hotkey", keys=st["keys"])
        elif d == "type":
            r = call("type_text", text=st["text"])
        elif d == "drag":
            r = call("drag_between", x1=int(st["x1"]), y1=int(st["y1"]), x2=int(st["x2"]), y2=int(st["y2"]), seconds=float(st.get("seconds", 0.4)))
        elif d == "wait":
            time.sleep(float(st["s"]))
            log.append({"step": i, "do": d, "ok": True})
            continue
        elif d == "shot":
            r = call("take_screenshot", out_path=str(home / st["path"]))
        elif d == "dialogs":
            r = call("list_open_dialogs")
        elif d == "recipe":
            r = call("run_gui_recipe", name=st["name"], params=st.get("params", {}))
        else:
            log.append({"step": i, "do": d, "ok": False, "error": "unknown step"})
            break
        row = {"step": i, "do": d, "ok": r.ok}
        row.update({"value": r.value} if r.ok else {"error": r.error.code, "message": r.error.message})
        log.append(row)
        if not r.ok:
            break
        time.sleep(float(st.get("after", spec.get("pause", 0.35))))
    final = call("take_screenshot", out_path=str(home / spec.get("shot", "sandbox/screens/gui_last.png")))
    dl = call("list_open_dialogs")
    print(json.dumps({"log": log, "shot": final.value if final.ok else final.error.message,
                      "dialogs": dl.value["dialogs"] if dl.ok else None}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
