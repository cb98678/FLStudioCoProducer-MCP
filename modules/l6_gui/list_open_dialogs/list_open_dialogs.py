from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def list_open_dialogs() -> Result:
    """List the windows FL Studio has open besides its main window (dialogs, plugin windows). Read only, no input is sent."""
    desk = get_service("desktop")
    if desk is None:
        return fail("E_UNSUPPORTED_API", "desktop control is not available")
    win = desk.find_window()
    if win is None:
        return fail("E_NOT_FOUND", "FL Studio's window was not found")
    others = [w for w in desk.windows_of_pid(win["pid"]) if w["handle"] != win["handle"]]
    return ok({"dialogs": [{"handle": w["handle"], "title": w["title"], "rect": list(w.get("rect") or [])} for w in others], "count": len(others)})
