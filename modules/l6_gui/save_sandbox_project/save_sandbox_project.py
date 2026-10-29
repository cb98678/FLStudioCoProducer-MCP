from __future__ import annotations

import time
from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def save_sandbox_project(project: str, wait_s: float = 15.0) -> Result:
    """Press Ctrl+S in FL Studio and confirm the saved file in the sandbox changed. Refuses unless the open project looks like that file.

    FL's script API cannot save and a render reads the saved file. The window title must contain the file's name.
    Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND, E_GUI_MISMATCH (another project is open), E_NOT_VERIFIED (file did not change).
    """
    chk = call("check_sandbox_path", path=project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    f = Path(chk.value["resolved"])
    if not f.is_file():
        return fail("E_NOT_FOUND", "no saved project at %s" % f)
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    if f.stem.lower() not in ready.value["title"].lower():
        return fail("E_GUI_MISMATCH", "the open window is titled %r, which does not name %s. Open the sandbox copy first." % (ready.value["title"], f.name))
    before = f.stat().st_mtime_ns
    pressed = call("press_hotkey", keys=["ctrl", "s"])
    if not pressed.ok:
        return pressed
    end = time.monotonic() + wait_s
    while time.monotonic() < end:
        try:    # FL replaces the file on save, so it can be missing for a moment
            if f.stat().st_mtime_ns != before:
                return ok({"path": str(f), "bytes": f.stat().st_size}, verified=True)
        except FileNotFoundError:
            pass
        time.sleep(0.25)
    return fail("E_NOT_VERIFIED", "Ctrl+S was sent but %s did not change within %.0f s; a dialog may be open" % (f.name, wait_s))
