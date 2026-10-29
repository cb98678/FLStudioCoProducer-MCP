from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def _checks(want: dict) -> dict:
    """Run each requested condition and return {name: bool}."""
    out = {}
    if "title_contains" in want:
        out["title_contains"] = want["title_contains"].lower() in call("check_desktop_ready").value["title"].lower()
    if "dialog_contains" in want or "no_dialog" in want:
        titles = [d["title"].lower() for d in call("list_open_dialogs").value["dialogs"]]
        if "dialog_contains" in want:
            out["dialog_contains"] = any(want["dialog_contains"].lower() in t for t in titles)
        if want.get("no_dialog"):
            out["no_dialog"] = not titles
    if "element" in want:
        out["element"] = call("locate_element", description=want["element"], min_confidence=want.get("min_confidence", 0.5)).ok
    return out


def screenshot_verify(expect: dict) -> Result:
    """Check the live window against expectations: title_contains, dialog_contains, no_dialog, element (needs the vision model).

    Errors: E_GUI_MISMATCH with the per-condition results when any condition fails.
    """
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    got = _checks(expect)
    if not got or not all(got.values()):
        return fail("E_GUI_MISMATCH", "the window does not match what was expected", checks=got)
    return ok({"checks": got, "all_passed": True})
