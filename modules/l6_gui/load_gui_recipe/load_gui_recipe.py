from __future__ import annotations

import json
from pathlib import Path

from coproducer.result import Result, fail, ok
from coproducer.services import get_service

KNOWN = ("hotkey", "type", "click", "click_row", "click_col", "template_click", "click_in_window", "locate_click", "wait", "expect_dialog", "expect_no_dialog", "expect_title", "expect_file")


def load_gui_recipe(name: str) -> Result:
    """Read one GUI recipe (a list of steps with checks) from the recipes folder and check its shape.

    Errors: E_NOT_FOUND, E_IO for unreadable JSON, E_ARG for an unknown step kind.
    """
    folder = get_service("recipes_dir")
    f = Path(folder) / (name + ".json") if folder else None
    if f is None or not f.is_file():
        return fail("E_NOT_FOUND", "no GUI recipe named %r" % name)
    try:
        rec = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return fail("E_IO", "cannot read recipe %s: %s" % (name, e))
    bad = [s.get("do") for s in rec.get("steps", []) if s.get("do") not in KNOWN]
    if bad or not rec.get("steps") or "params" not in rec:
        return fail("E_ARG", "recipe %s has unknown step kinds %s or is incomplete" % (name, bad))
    return ok({"verified": False, **rec})
