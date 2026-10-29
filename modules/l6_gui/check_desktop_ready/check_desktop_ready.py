from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def check_desktop_ready() -> Result:
    """Check that input may be sent: not halted, FL Studio's window exists and has focus, display scale matches the record.

    Errors: E_HALTED, E_UNSUPPORTED_API (no desktop backend), E_NOT_FOUND (no FL window), E_GUI_MISMATCH (focus or scale).
    Returns the window handle, size and title. Every input primitive calls this first.
    """
    halt, desk, cfg = get_service("halt"), get_service("desktop"), get_service("desktop_config") or {}
    if halt is not None and halt.is_set():
        return fail("E_HALTED", "input is halted")
    if desk is None:
        return fail("E_UNSUPPORTED_API", "desktop control is not available; it needs the interactive Windows session")
    win = desk.find_window()
    if win is None:
        return fail("E_NOT_FOUND", "FL Studio's main window was not found (only its startup or another dialog may be open; close it or open a project)")
    if desk.foreground()["pid"] == 0:
        return fail("E_GUI_MISMATCH", "no window has the focus at all: the screen is probably locked or asleep; unlock it", locked=True)
    if desk.foreground()["pid"] != win["pid"] and not desk.focus(win["handle"]):
        return fail("E_GUI_MISMATCH", "another program has the focus and FL Studio would not take it", foreground=desk.foreground()["title"])
    scale, want = desk.scale(win["handle"]), cfg.get("display_scale", 0.0)
    if want and abs(scale - want) > 0.01:
        return fail("E_GUI_MISMATCH", "display scale is %.2f but anchors were recorded at %.2f" % (scale, want))
    left, top, right, bottom = win["rect"]
    return ok({"handle": win["handle"], "pid": win["pid"], "title": win["title"], "left": left, "top": top,
               "width": right - left, "height": bottom - top, "scale": scale})
