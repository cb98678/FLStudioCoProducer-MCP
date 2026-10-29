from __future__ import annotations

import time

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _bridge_back(wait_s: float) -> bool:
    end = time.monotonic() + wait_s
    while time.monotonic() < end:
        if call("ping_fl").ok:
            return True
        time.sleep(1.0)
    return False


def render_with_restart(project: str, out_dir: str, wait_s: float = 120.0) -> Result:
    """Render a saved sandbox project to WAV: close FL, run the command-line render, start FL again on the project, wait for the bridge.

    FL's command line only renders when no FL copy is running. Closing is graceful and refused when the project has unsaved changes. Autonomy A1:
    closing FL is the person's call, so a run asks before each use (the person running a coproducer probe command is that approval).
    Errors: E_SANDBOX_VIOLATION, E_UNSUPPORTED_API, E_NOT_VERIFIED (unsaved), E_BLOCKED_BY_DIALOG (FL did not close), E_TIMEOUT, render errors.
    """
    procs, exe, root = get_service("procs"), get_service("fl_exe"), str(get_service("sandbox_root"))
    for p in (project, out_dir):
        chk = call("check_sandbox_path", path=p, sandbox_root=root)
        if not chk.ok:
            return chk
    if procs is None or not exe:
        return fail("E_UNSUPPORTED_API", "needs process control and a configured FL executable (Windows)")
    if procs.fl_count():
        dirty = call("op_general_get_changed_flag")
        if not dirty.ok or dirty.value:
            return fail("E_NOT_VERIFIED", "the open project has unsaved changes or its state could not be read; save it first (nothing was closed)")
        if not procs.close_fl(30.0):
            return fail("E_BLOCKED_BY_DIALOG", "FL did not close within 30 s; a dialog may be open")
    rendered = call("render_via_cli", project=project, out_dir=out_dir)
    procs.launch(exe, project)
    began = time.monotonic()
    back = _bridge_back(wait_s)
    if not rendered.ok:
        return rendered
    if not back:
        return fail("E_TIMEOUT", "rendered %s but the bridge did not answer within %.0f s after restarting FL" % (rendered.value["path"], wait_s), path=rendered.value["path"])
    return ok({**rendered.value, "restarted": True, "bridge_back_s": round(time.monotonic() - began, 1)}, verified=True)
